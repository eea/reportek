import re
import logging
from functools import wraps
import enum
from django.db import models
from django.utils.functional import cached_property
from django.contrib.contenttypes.fields import GenericRelation
from typedmodels.models import TypedModel
import xworkflows as xwf
import networkx as nx

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

import attr

from reportek.core.tasks import submit_xml_to_qa
from reportek.core.consumers.envelope import EnvelopeEvents

from .log import TransitionEvent
from ...utils import is_proper_sequence


log = logging.getLogger('reportek.workflows')
info = log.info
debug = log.debug
warn = log.warning
error = log.error


CLASS_NAME_PATTERN = re.compile('[\W_]+')


@enum.unique
class WorkflowActors(enum.IntEnum):
    """
    Workflow actors encode the types of entities that can act on a workflow.
    """
    SYSTEM = 0  # Used by automatic transitions
    ADMIN = 1  # Workflow managers, support, etc.
    REPORTER = 2  # Users reporting on an obligation
    CLIENT = 3  # Users acting as client representatives
    AUDITOR = 4  # Users acting as delivery auditors

    @classmethod
    def has_value(cls, value):
        return any(value == item.value for item in cls)


@attr.s(hash=True)
class WorkflowState:
    """
    Workflow states.
    """
    name = attr.ib(validator=attr.validators.instance_of(str))
    title = attr.ib(validator=attr.validators.instance_of(str))


def is_callable(instance, attribute, value):
    if not callable(value):
        raise TypeError('Expected a callable')


def is_states_seq(instance, attribute, value):
    if not is_proper_sequence(value) or not all(
        isinstance(el, WorkflowState) for el in value
    ):
        raise TypeError('Expected WorkflowState sequence')


def is_actors_list(instance, attribute, value):
    if not is_proper_sequence(value) or not all(
        WorkflowActors.has_value(el) for el in value
    ):
        raise TypeError('Expected WorkflowActors sequence')


@attr.s()
class WorkflowTransition:
    """
    Workflow transitions are defined by:
        - a name - will be set on the implementation method
        - the implementation - a method containing the work to be performed
        - the source states - a list of `WorkflowState`s
        - the target state - a `WorkflowState`
        - the actors allowed to perform the transition - a list of `WorkflowActors`
    """

    name = attr.ib(validator=attr.validators.instance_of(str))
    implementation = attr.ib(validator=is_callable)
    target = attr.ib(validator=attr.validators.instance_of(WorkflowState))
    on_enter_target = attr.ib(
        default=None, validator=attr.validators.optional(validator=is_callable)
    )
    sources = attr.ib(attr.Factory(tuple), validator=is_states_seq)
    allowed_actors = attr.ib(
        default=(WorkflowActors.SYSTEM, WorkflowActors.ADMIN), validator=is_actors_list
    )


class BaseWorkflow(TypedModel):
    """
    Base class for workflows.
    Workflows are implemented as concrete types based on this.
    """

    name = models.CharField(max_length=100)
    previous_state = models.CharField(max_length=60, null=True, blank=True)
    current_state = models.CharField(max_length=60, null=True, blank=True)
    history = GenericRelation(TransitionEvent)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'core_workflow'
        verbose_name = 'workflow'

    class TransitionDoesNotExistError(Exception):
        pass

    class TransitionNotAvailableError(Exception):
        pass

    class MisconfiguredWorkflowError(Exception):
        pass

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.current_state = self.current_state or self.initial_state.name
        super().save(*args, **kwargs)

    # While concrete types CAN set `states` explicitly,
    # they can be left empty and the workflow will derive
    # them from the transitions.
    states = ()  # WorkflowState tuple

    # Concrete types MUST set these; see `ReferenceWorkflow`
    transitions = ()  # WorkflowTransition tuple
    initial_state = None  # The initial WorkflowState
    final_state = None  # The final WorkflowState
    upload_states = ()  # The WorkflowState's that allow uploading

    # When set, envelopes will be unassigned after each transition
    unassign_after_transition = True

    @property
    def finished(self):
        return self.current_state == self.final_state.name

    @property
    def upload_allowed(self):
        return self.envelope.assigned_to is not None \
               and self.current_state in self.upload_states_names()

    @property
    def available_transitions(self):
        """
        Property returning the list of available transitions from the current state.
        Availability takes into account the workflow's checks.
        """
        # Skip all
        if self.envelope.assigned_to == self.system_user:
            return []

        state = self.xwf.state.workflow.states[self.current_state]
        return [
            t.name
            for t in self.xwf.state.workflow.transitions
            if state.name in [s.name for s in t.source]
            and getattr(self.xwf, t.name).is_available()  # ImplementationWrapper
        ]

    @classmethod
    def gather_states(cls):
        """
        Generates a tuple of the unique `WorkflowState`s used in `transactions`.
        """
        states = set()
        for t in cls.transitions:
            states.update(set(src for src in t.sources))
            states.add(t.target)
        return tuple(states)

    @classmethod
    def state_names(cls):
        states = cls.states or cls.gather_states()
        return tuple(s.name for s in states)

    @classmethod
    def transition_names(cls):
        return tuple(t.name for t in cls._transitions)

    @classmethod
    def upload_states_names(cls):
        return tuple(s.name for s in cls.upload_states)

    @classmethod
    def get_digraph(cls):
        graph = nx.DiGraph()
        for t in cls.transitions:
            for src in t.sources:
                graph.add_edge(src.name, t.target.name)
        return graph

    @classmethod
    def validate_workflow(cls):
        """
        Validates the workflow.

        Checks performed:
         - `initial_state` is in `states`
         - `final_state` is in `states`
         - there is a single possible end state, and it is `final_state`.
        """
        states = cls.states or cls.gather_states()
        if cls.initial_state not in states:
            raise cls.MisconfiguredWorkflowError(
                f'Invalid workflow configuration: initial state {cls.initial_state.name} '
                f'not in `states`: {cls.state_names()}'
            )

        if cls.final_state not in states:
            raise cls.MisconfiguredWorkflowError(
                f'Invalid workflow configuration: final state {cls.initial_state.name} '
                f'not in `states`: {cls.state_names()}'
            )

        digraph = cls.get_digraph()
        expected_end_state = cls.final_state.name
        end_states = list(nx.attracting_components(digraph))
        if end_states != [{expected_end_state}]:
            raise cls.MisconfiguredWorkflowError(
                f'Invalid workflow configuration: end state(s) = {end_states} '
                f'but only "{expected_end_state}" is allowed.'
            )

    def submit_xml_to_qa(self):
        """
        Sends the envelope to QA, providing the result callback.
        """
        return submit_xml_to_qa(self.envelope.pk)

    def handle_auto_qa_results(self, *args, **kwargs):
        """
        Concrete types must implement this with the post-QA logic
        (i.e. to trigger an automatic transition).
        """
        raise NotImplementedError

    def announce_auto_qa_status(self, event):
        channel_layer = get_channel_layer()
        payload = {
            'auto_qa_complete': self.envelope.auto_qa_complete,
            'auto_qa_ok': self.envelope.auto_qa_ok,
        }
        async_to_sync(channel_layer.group_send)(
            self.envelope.channel, {'type': f'envelope.{event.name}', 'data': payload}
        )

    def _make_xwf_cls_name(self):
        """Builds a cleaned-up name for the XWorkflow class"""
        return f'XWFDef_{re.sub(CLASS_NAME_PATTERN, "", self.name.capitalize())}'

    def _get_xwf_states(self):
        """Prepares the state tuple definitions as used by XWorrkflow."""
        states = self.states or self.gather_states()
        return tuple((s.name, s.title) for s in states)

    def _get_xwf_transitions(self):
        """Prepares the transition tuple definitions as used by XWorrkflow."""
        return tuple(
            (t.name, tuple(s.name for s in t.sources), t.target.name)
            for t in self.transitions
        )

    @property
    def xwf_cls(self):
        """
        Builds a custom XWorkflow class from the concrete type's specs.
        """

        def log_transition(self, transition, from_state, workflow):
            """
            Transition event logger - supplied to the XWorkflow class.
            """
            trans, src, dst = transition.name, from_state, workflow.state
            info(f'Envelope {self.bearer.envelope.name} completed transition "{trans}" '
                 f'from "{src}" to "{dst}"')
            TransitionEvent.objects.create(
                content_object=self.bearer,
                transition=trans,
                from_state=src,
                to_state=dst,
            )

        self.validate_workflow()

        bases = (xwf.Workflow,)
        attrs = {
            'bearer': self,
            'envelope': self.envelope,
            'states': self._get_xwf_states(),
            'transitions': self._get_xwf_transitions(),
            'initial_state': self.initial_state.name,
            'log_transition': log_transition,
        }

        return type(self._make_xwf_cls_name(), bases, attrs)

    def _get_xwf_transition_methods(self):
        """
        Gathers transition implementations from `WorkflowTransition` instances
        in `transitions`, and applies `TransisionWrapper` on them.

        Returns:
            dict of transition names and implementations.
        """
        implementations = {
            t.name: xwf.transition(t.name)(t.implementation)
            for t in self.transitions
            if callable(t.implementation)
        }
        return implementations

    def _get_xwf_hook_methods(self):
        """
        Gathers `on_enter` hook implementations from `WorkflowTransition` instances
        in `transitions`, and applies the `on_enter_state` wrapper on them.

        Returns:
             dict of hook names and implementations.
        """
        implementations = {
            f'hook_on_enter_state_{t.target.name}': xwf.on_enter_state(t.target.name)(
                t.on_enter_target
            )
            for t in self.transitions
            if callable(t.on_enter_target)
        }
        return implementations

    def _get_xwf_concrete_methods(self):
        """
        Gets the transition and hook methods from the concrete workflow class.

        XWorkflows methods are identified based on the effects of their decorators:
        - @transition wraps methods in a TransisionWrapper
        - hook decorators (@before|after_transition, @on_enter|leave_state)
          set a `xworkflows_hook` attribute on the method
        """

        cls = self.__class__
        implementations = {
            fname: getattr(cls, fname)
            for fname in dir(cls)
            if callable(getattr(cls, fname))
            and (
                isinstance(getattr(cls, fname), xwf.base.TransitionWrapper)
                or hasattr(getattr(cls, fname), 'xworkflows_hook')
            )
        }
        return implementations

    def _get_xwf_methods(self):
        """
        Builds an 'attrs'-style dict of transition & hook methods.
        """
        methods = {}
        methods.update(self._get_xwf_transition_methods())
        methods.update(self._get_xwf_hook_methods())
        methods.update(self._get_xwf_concrete_methods())
        return methods

    def _make_xwf_enabled_cls_name(self):
        """Builds a cleaned-up name for the inner XWorkflow-enabled class"""
        return f'XWFEnabled_{re.sub(CLASS_NAME_PATTERN, "", self.name.capitalize())}'

    @property
    def xwf(self):
        """
        Builds a workflow-enabled class and returns an instance set to the current state.
        """

        def transition_check_if_assigned(self, *args, **kwargs):
            return self.bearer.envelope.is_assigned

        def post_transition(self, *args, **kwargs):
            """After transition hook applied to all workflows"""

            wflow = self.bearer  # Get at the workflow model instance

            debug(f'Persisting state change to "{self.state.name}".')
            wflow.previous_state = wflow.current_state
            wflow.current_state = self.state.name
            wflow.save()

            if wflow.unassign_after_transition:
                wflow.envelope.assigned_to = None
                wflow.envelope.save()
                info(f'Envelope "{self.bearer.envelope.name}" was unassigned')

            if wflow.finished:
                wflow.envelope.finalized = True
                wflow.envelope.save()
                info(f'Envelope "{self.bearer.envelope.name}" has been finalized.')
            elif wflow.envelope.finalized:
                wflow.envelope.finalized = False
                wflow.envelope.save()
                info(f'Envelope "{self.bearer.envelope.name}" is no longer finalized.')

            channel_layer = get_channel_layer()
            payload = {
                'previous_state': wflow.previous_state,
                'current_state': wflow.current_state,
                'finalized': wflow.envelope.finalized,
            }
            async_to_sync(channel_layer.group_send)(
                wflow.envelope.channel,
                {
                    'type': f'envelope.{EnvelopeEvents.ENTERED_STATE.name}',
                    'data': payload,
                },
            )

        # Transplant the transition methods
        attrs = self._get_xwf_methods()
        attrs.update(
            {
                'state': self.xwf_cls(),
                'bearer': self,
                'transition_check': xwf.transition_check()(transition_check_if_assigned),
                # Post hooks (after_transition & on_enter) are run in priority order.
                # This makes sure `post_transition` runs before others.
                # DO NOT alter this, or things like automatic transitions will skip
                # the current transaction's post.
                'post_transition': xwf.after_transition(priority=1000)(post_transition),
                # XWorkflows needs __module__ set on the enabled class
                '__module__': __name__
            }
        )
        cls = type(self._make_xwf_enabled_cls_name(), (xwf.WorkflowEnabled,), attrs)
        wf = cls()
        wf.state = self.current_state  # Force to current state
        return wf

    def inspect_xwf_hooks(self, transition):
        """
        Returns the hooks available on the XWorkflow instance for `transition`.
        """
        return self.xwf._xworkflows_implems['state'].implementations[transition].hooks

    def start_transition(self, name):
        """Starts a transition on the inner XWorkflow"""
        wf = self.xwf
        if name not in [t.name for t in wf.state.workflow._transitions]:
            raise self.TransitionDoesNotExistError('Invalid transition name')

        if name not in [t.name for t in wf.state._transitions()]:
            raise self.TransitionNotAvailableError(
                'Transition not allowed from current state'
            )

        transition = getattr(wf, name)

        if not transition.is_available():
            raise self.TransitionNotAvailableError('Transition checks not satisfied')

        transition()

    def to_json_graph(self):
        """
        Represents the workflow as a dictionary conformant to JSON graph.
        (https://github.com/jsongraph/json-graph-specification)
        """
        nodes = []
        for _state in self._states:
            state, title = _state
            node = {
                'id': state,
                'label': title,
                'metadata': {
                    'initial': state == self.initial_state.name,
                    'final': state == self.final_state.name,
                    'current': state == self.current_state,
                },
            }
            nodes.append(node)

        edges = []
        for transition in self._transitions:
            name, src, tgt = transition
            # XWorkflows transitions can have multiple source states
            if isinstance(src, tuple):
                for _src in src:
                    edges.append({
                        'id': name,
                        'label': name,
                        'source': _src,
                        'target': tgt
                    })
            else:
                edges.append({
                    'id': name,
                    'label': name,
                    'source': src,
                    'target': tgt
                })

        return {
            'graph': {
                'directed': True,
                'rankdir': 'LR',
                'nodes': nodes,
                'edges': edges
            }
        }


def as_system(f):
    """
    Transition method wrapper that first assigns the envelope to the system user.
    For use with automatic transitions to avoid failing the assignment check.
    """
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        self.bearer.envelope.assign_to_system()
        return f(self, *args, **kwargs)
    return wrapper
