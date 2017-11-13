import re
from django.db import models
from django.utils.functional import cached_property
from django.contrib.contenttypes.fields import GenericRelation
from typedmodels.models import TypedModel
import xworkflows as xwf

from reportek.core.models.reporting import Envelope
from reportek.core.qa import QAConnection
from .log import TransitionEvent


class BaseWorkflow(TypedModel):
    """
    Base class for workflows.
    Workflows are implemented as concrete types based on this.
    """

    name = models.CharField(max_length=100)
    previous_state = models.CharField(max_length=60, null=True)
    current_state = models.CharField(max_length=60)
    envelope = models.ForeignKey(Envelope)
    history = GenericRelation(TransitionEvent)

    class Meta:
        verbose_name = 'workflow'

    def __str__(self):
        return self.name

    # Concrete types must specify these per the XWorkflows API
    states = ()
    transitions = ()
    initial_state = None

    # NOTE: The QA connection is only a mock currently
    qa_conn = QAConnection()

    def submit_to_qa(self):
        """
        Sends the envelope to QA, providing the result callback.
        """
        return self.qa_conn.send(
            self.envelope,
            self.handle_qa_result
        )

    def handle_qa_result(self, result):
        """
        Concrete types must implement this with the post-QA logic
        (i.e. to trigger an automatic transition).
        """
        raise NotImplementedError

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
            print(f'Logging transition "{trans}"')
            TransitionEvent.objects.create(
                content_object=self.bearer,
                transition=trans,
                from_state=src,
                to_state=dst
            )
            print(f'"{self.envelope.name}" is now in state "{dst}".')

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
    def transition_methods(self):
        """Builds an 'attrs'-style dict of transition methods"""
        cls = self.__class__
        return {
            fname: getattr(cls, fname)
            for fname in dir(cls)
            if callable(getattr(cls, fname)) and
            isinstance(getattr(cls, fname), xwf.base.TransitionWrapper)
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

        def post_transition(self, *args, **kwargs):
            """After transition hook applied to all workflows"""
            print(f'Persisting state change to "{self.state.name}".')
            # Persist state
            self.bearer.previous_state = self.bearer.current_state
            self.bearer.current_state = self.state.name
            self.bearer.save()

        # Transplant the transition methods
        attrs = self.transition_methods
        attrs.update(
            {
                'state': self.xwf_cls(),
                'bearer': self,
                'envelope': self.envelope,
                'qa_conn': self.qa_conn,
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
