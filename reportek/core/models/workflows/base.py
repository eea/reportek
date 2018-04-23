import logging
from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from typedmodels.models import TypedModel
import xworkflows as xwf

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from reportek.core.tasks import submit_xml_to_qa
from reportek.core.consumers.envelope import EnvelopeEvents

from .bearer import XWorkflowBearerMixin
from .exceptions import (
    TransitionDoesNotExistError,
    TransitionNotAvailableError,
    StateDoesNotExistError,
)
from .log import TransitionEvent


log = logging.getLogger('reportek.workflows')
info = log.info
debug = log.debug
warn = log.warning
error = log.error


class BaseWorkflow(XWorkflowBearerMixin, TypedModel):
    """
    Base class for workflows, provides single table storage and XWorkflows features.

    Non-field attributes:

         `upload_states` (`WorkflowState` tuple): states during which uploading is
            allowed.

         `unassign_after_transition` (default `True`): if on, the envelope will be
            unassigned post-transition.

         `finalize_on_end_state` (default `True`): if on, the envelope is finalized
            when the workflow enters its last state.

    """

    name = models.CharField(max_length=100)
    previous_state = models.CharField(max_length=60, null=True, blank=True)
    current_state = models.CharField(max_length=60, null=True, blank=True)
    history = GenericRelation(TransitionEvent)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    upload_states = ()  # The WorkflowState's that allow uploading

    unassign_after_transition = True

    finalize_on_end_state = True

    class Meta:
        db_table = 'core_workflow'
        verbose_name = 'workflow'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.current_state = self.current_state or self.initial_state.name
        super().save(*args, **kwargs)

    def force_state(self, state):
        """Workflow management method, forcefully sets the current state."""
        if state not in self.state_names():
            raise StateDoesNotExistError(f'Unknown state: {state}')

        self.current_state = state
        self.save()

    @property
    def finished(self):
        return self.current_state == self.final_state.name

    @classmethod
    def upload_states_names(cls):
        return tuple(s.name for s in cls.upload_states)

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

    @classmethod
    def get_transition_logger(cls):
        def log_transition(self, transition, from_state, workflow):
            """
            Transition event logger - supplied to the XWorkflow class.
            """
            trans, src, dst = transition.name, from_state, workflow.state
            info(f'Envelope "{self.bearer.envelope.name}" completed transition "{trans}" '
                 f'from "{src}" to "{dst}"')
            TransitionEvent.objects.create(
                content_object=self.bearer,
                transition=trans,
                from_state=src,
                to_state=dst,
            )

        return log_transition

    @xwf.transition_check()
    def transition_check_if_assigned(self, *args, **kwargs):
        return self.bearer.envelope.is_assigned

    @xwf.after_transition(priority=1000)
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
            if wflow.finalize_on_end_state:
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

    def start_transition(self, name):
        """Starts a transition on the inner XWorkflow"""
        wf = self.xwf
        if name not in self.transition_names():
            raise TransitionDoesNotExistError(f'Unknown transition: {name}')

        if name not in [t.name for t in wf.state.transitions()]:
            raise TransitionNotAvailableError(
                f'Transition "{name}" is not possible from state "{self.current_state}"'
            )

        transition = getattr(wf, name)

        if not transition.is_available():
            raise self.TransitionNotAvailableError(
                f'Transition checks not satisfied for "{name}"'
            )

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

