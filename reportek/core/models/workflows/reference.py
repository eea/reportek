import logging
# import xworkflows as xwf

from .base import BaseWorkflow
from .common.states import Draft, End
from .common.transitions import *

__all__ = [
    'ReferenceWorkflow',
]

log = logging.getLogger('reportek.workflows')
info = log.info
debug = log.debug
warn = log.warning
error = log.error


class ReferenceWorkflow(BaseWorkflow):

    transitions = (
        DeleteAQAResults,
        SendToAQA,
        PassAutoQA,
        FailAutoQA,
        PingCR,
        RestrictAQAResults,
        ConfirmReceipt,
        Release,
        RequestFinalFeedback,
        RevokeRelease,
        RequestCorrection,
        ReleaseAQAResults,
        TechnicallyAccept,
        Complete
    )

    initial_state = Draft
    final_state = End
    upload_states = [Draft]

    unassign_after_transition = False

    class Meta:
        verbose_name = 'Workflow - Reference'
        verbose_name_plural = 'Workflows - Reference'

