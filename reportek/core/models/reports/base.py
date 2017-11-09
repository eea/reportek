from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from typedmodels.models import TypedModel
from django_xworkflows.models import (
    GenericTransitionLog,
)

# We want WorkflowEnabled from xworkflows,
# rather the same-name class from django_xworkflows
# (the latter is model-based and comes with too much
# django baggage)
from xworkflows import WorkflowEnabled
from xworkflows.base import TransitionWrapper

from reportek.core.models import (
    Country,
    Obligation,
)
from reportek.core.models.workflows import (
    WorkFlow,
    WFState,
    WFTransition,
)
from .log import ReportLog


class TransitionLog(GenericTransitionLog):
    pass


class BaseReport(TypedModel):
    name = models.CharField(max_length=100)
    obligation = models.ForeignKey(Obligation)
    country = models.ForeignKey(Country)
    workflow = models.ForeignKey(WorkFlow)
    wf_state = models.ForeignKey(WFState)
    log_events = GenericRelation(ReportLog)

    class Meta:
        db_table = 'core_reports'

    def __str__(self):
        return self.name

    def get_transition_methods(self):
        """Builds an 'attrs'-style dict of transition methods"""
        # Pick the transitions from the class not the instance,
        # to avoid running into the Django Manager getattr error
        cls = self.__class__
        return {
            fname: getattr(cls, fname)
            for fname in dir(cls)
            if callable(getattr(cls, fname)) and
            isinstance(getattr(cls, fname), TransitionWrapper)
        }

    @property
    def xwf(self):
        """
        Builds a workflow-enabled instance and brings it to the current state
        of the report.
        """
        # Prepare a XWorkflow class
        xwf_cls = self.workflow.make_xworkflow_cls()
        # A class and instance bearing the workflow is built on the fly
        # Transplant the transition methods
        attrs = self.get_transition_methods()
        attrs['report'] = self
        attrs['state'] = xwf_cls()
        attrs['__module__'] = __name__  # XWorkflows wants __module__ set
        cls_name = f'{self.name.replace(" ", "").capitalize()}WF'
        wf_bearer = type(
            cls_name,
            (WorkflowEnabled,),
            attrs)
        wf = wf_bearer()
        wf.state = self.wf_state.name  # Move to current state
        return wf

    def log_transition(self, transition_name, from_state, to_state, extra=None):
        transition = WFTransition.objects.get(
            name=transition_name,
            workflow=self.workflow
        )
        ReportLog.objects.create(
            content_object=self,
            transition=transition,
            from_state=from_state,
            to_state=to_state,
            extra=extra
        )
