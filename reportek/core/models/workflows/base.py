import re
import logging
from django.db import models
from django.utils.functional import cached_property
from django.contrib.contenttypes.fields import GenericRelation
from typedmodels.models import TypedModel
import xworkflows as xwf

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from reportek.core.tasks import submit_xml_to_qa
from reportek.core.consumers.envelope import EnvelopeEvents

from .log import TransitionEvent


log = logging.getLogger('reportek.workflows')
info = log.info
debug = log.debug
warn = log.warning
error = log.error


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

    class TransitionDoesNotExist(Exception):
        pass

    class TransitionNotAvailable(Exception):
        pass

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.current_state = self.current_state or self.initial_state
        super().save(*args, **kwargs)

    # Concrete types must specify these per the XWorkflows API
    states = ()
    transitions = ()
    initial_state = None
    final_state = None
    upload_states = []

    # When set, envelopes will be unassigned after each transition
    unassign_after_transition = True

    @property
    def finished(self):
        return self.current_state == self.final_state

    @property
    def upload_allowed(self):
        return self.current_state in self.upload_states

    @property
    def available_transitions(self):
        """
        Property returning the list of available transitions from the current state.
        Availability takes into account the workflow's checks.
        """
        state = self.xwf.state.workflow.states[self.current_state]
        return [
            t.name
            for t in self.xwf.state.workflow.transitions
            if state.name in [s.name for s in t.source]
            and getattr(self.xwf, t.name).is_available()  # ImplementationWrapper
        ]

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
            self.envelope.channel,
            {
                'type': f'envelope.{event.name}',
                'data': payload
            }
        )

    @cached_property
    def xwf_cls_name(self):
        """Builds a cleaned-up name for the XWorkflow class"""
        pattern = re.compile('[\W_]+')
        return f'XWFDef_{re.sub(pattern, "", self.name.capitalize())}'

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
            info(f'Logging transition "{trans}"')
            TransitionEvent.objects.create(
                content_object=self.bearer,
                transition=trans,
                from_state=src,
                to_state=dst
            )
            info(f'"{self.bearer.envelope.name}" is now in state "{dst}".')

        bases = (xwf.Workflow,)
        attrs = {
            'bearer': self,
            'envelope': self.envelope,
            'states': self.states,
            'transitions': self.transitions,
            'initial_state': self.initial_state,
            'log_transition': log_transition
        }

        return type(self.xwf_cls_name, bases, attrs)

    # Resist the temptation to cache this - it will noop the XWF transitions
    @property
    def xwf_methods(self):
        """
        Builds an 'attrs'-style dict of transition & hook methods.

        XWorkflows methods are identified based on the effects of their decorators:
        - @transition wraps methods in a TransisionWrapper
        - hook decorators (@before|after_transition, @on_enter|leave_state)
          set a `xworkflows_hook` attribute on the method
        """
        cls = self.__class__
        return {
            fname: getattr(cls, fname)
            for fname in dir(cls)
            if callable(getattr(cls, fname)) and (
                isinstance(getattr(cls, fname), xwf.base.TransitionWrapper) or
                hasattr(getattr(cls, fname), 'xworkflows_hook')
            )
        }

    @cached_property
    def xwf_enabled_cls_name(self):
        """Builds a cleaned-up name for the inner XWorkflow-enabled class"""
        pattern = re.compile('[\W_]+')
        return f'XWFEnabled_{re.sub(pattern, "", self.name.capitalize())}'

    @property
    def xwf(self):
        """
        Builds a workflow-enabled class and returns an instance set to the current state.
        """

        def transition_check_if_assigned(self, *args, **kwargs):
            return self.bearer.envelope.is_assigned

        def post_transition(self, *args, **kwargs):
            """After transition hook applied to all workflows"""

            info(f'Persisting state change to "{self.state.name}".')
            # Persist state
            self.bearer.previous_state = self.bearer.current_state
            self.bearer.current_state = self.state.name
            self.bearer.save()
            if self.bearer.unassign_after_transition:
                self.bearer.envelope.assigned_to = None
                self.bearer.envelope.save()
            # Mark envelope as finazized when workflow is done
            if self.bearer.finished:
                self.bearer.envelope.finalized = True
                self.bearer.envelope.save()
                info(f'Envelope "{self.bearer.envelope.name}" has been finalized.')
            elif self.bearer.envelope.finalized:
                self.bearer.envelope.finalized = False
                self.bearer.envelope.save()
                info(f'Envelope "{self.bearer.envelope.name}" is no longer finalized.')

            channel_layer = get_channel_layer()
            payload = {
                'previous_state': self.bearer.previous_state,
                'current_state': self.bearer.current_state,
                'finalized': self.bearer.envelope.finalized
            }
            async_to_sync(channel_layer.group_send)(
                self.bearer.envelope.channel,
                {
                    'type': f'envelope.{EnvelopeEvents.ENTERED_STATE.name}',
                    'data': payload
                }
            )

        # Transplant the transition methods
        attrs = self.xwf_methods
        attrs.update(
            {
                'state': self.xwf_cls(),
                'bearer': self,
                'transition_check': xwf.transition_check()(transition_check_if_assigned),
                'post_transition': xwf.after_transition()(post_transition),
                # XWorkflows needs __module__ set on the enabled class
                '__module__': __name__
            }
        )
        cls = type(
            self.xwf_enabled_cls_name,
            (xwf.WorkflowEnabled,),
            attrs)
        wf = cls()
        wf.state = self.current_state  # Force to current state
        return wf

    def start_transition(self, name):
        """Starts a transition on the inner XWorkflow"""
        wf = self.xwf
        if name not in [t.name for t in wf.state.workflow.transitions]:
            raise self.TransitionDoesNotExist('Invalid transition name')

        if name not in [t.name for t in wf.state.transitions()]:
            raise self.TransitionNotAvailable('Transition not allowed from current state')

        transition = getattr(wf, name)

        if not transition.is_available():
            raise self.TransitionNotAvailable('Transition checks not satisfied')

        transition()

    def to_json_graph(self):
        """
        Represents the workflow as a dictionary conformant to JSON graph.
        (https://github.com/jsongraph/json-graph-specification)
        """
        nodes = []
        for _state in self.states:
            state, title = _state
            node = {
                'id': state,
                'label': title,
                'metadata': {
                    'initial': state == self.initial_state,
                    'final': state == self.final_state,
                    'current': state == self.current_state
                }
            }
            nodes.append(node)

        edges = []
        for transition in self.transitions:
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
