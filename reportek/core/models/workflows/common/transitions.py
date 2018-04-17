import logging
from functools import wraps
from ..base import WorkflowTransition, WorkflowActors, as_system
from .states import *

log = logging.getLogger('reportek.workflows')
info = log.info
debug = log.debug
warn = log.warning
error = log.error

__all__ = [
    'DeleteAQAResults',
    'SendToAQA',
    'PassAutoQA',
    'FailAutoQA',
    'PingCR',
    'RestrictAQAResults',
    'ConfirmReceipt',
    'Release',
    'RequestFinalFeedback',
    'RevokeRelease',
    'RequestCorrection',
    'ReleaseAQAResults',
    'TechnicallyAccept',
    'Complete'
]


def auto_start_transition(transition):
    """
    Automatic transition hook factory.
    Returns a handler that automatically triggers `transition`.
    """

    @as_system
    def _auto_transition(self, *args, **kwargs):
        info(f'Automatic transition "{transition}"')
        getattr(self, transition)()

    return _auto_transition


def mock_transition(method):
    """
    Transition implementation decorator, turns it into a noop for mock purposes.
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        info(f'>>> Mock-running transition method "{method.__name__}"')
    return wrapper


@mock_transition
def delete_auto_qa_results(self):
    pass


DeleteAQAResults = WorkflowTransition(
    name='delete_auto_qa_results',
    sources=(Draft,),
    target=AQAResultsDeleted,
    implementation=delete_auto_qa_results,
    allowed_actors=(WorkflowActors.REPORTER,),
    on_enter_target=auto_start_transition('send_to_auto_qa'),
)


@mock_transition
def send_to_auto_qa(self):
    pass


SendToAQA = WorkflowTransition(
    name='send_to_auto_qa',
    sources=(AQAResultsDeleted,),
    target=AQAPending,
    implementation=send_to_auto_qa,
)


@mock_transition
def pass_auto_qa(self):
    pass


PassAutoQA = WorkflowTransition(
    name='pass_auto_qa',
    sources=(AQAPending,),
    target=AQAPassed,
    implementation=pass_auto_qa,
    on_enter_target=auto_start_transition('ping_cr'),
)


@mock_transition
def fail_auto_qa(self):
    pass


FailAutoQA = WorkflowTransition(
    name='fail_auto_qa',
    sources=(AQAPending,),
    target=AQAFailed,
    implementation=fail_auto_qa,
    on_enter_target=auto_start_transition('ping_cr'),
)


@mock_transition
def ping_cr(self):
    pass


PingCR = WorkflowTransition(
    name='ping_cr',
    sources=(AQAPassed, AQAFailed),
    target=CRPinged,
    implementation=ping_cr,
    on_enter_target=auto_start_transition('restrict_auto_qa_results'),
)


@mock_transition
def restrict_auto_qa_results(self):
    pass


RestrictAQAResults = WorkflowTransition(
    name='restrict_auto_qa_results',
    sources=(CRPinged,),
    target=AQAResultsRestricted,
    implementation=restrict_auto_qa_results,
    on_enter_target=auto_start_transition('confirm_receipt'),
)


@mock_transition
def confirm_receipt(self):
    pass


ConfirmReceipt = WorkflowTransition(
    name='confirm_receipt',
    sources=(AQAResultsRestricted,),
    target=ReceiptConfirmed,
    implementation=confirm_receipt,
)


@mock_transition
def release(self):
    pass


Release = WorkflowTransition(
    name='release',
    sources=(ReceiptConfirmed,),
    target=Released,
    implementation=release,
)


@mock_transition
def request_final_feedback(self):
    pass


RequestFinalFeedback = WorkflowTransition(
    name='request_final_feedback',
    sources=(Released,),
    target=FinalFeedback,
    implementation=request_final_feedback,
)


@mock_transition
def revoke_release(self):
    pass


RevokeRelease = WorkflowTransition(
    name='revoke_release',
    sources=(FinalFeedback,),
    target=Draft,
    implementation=revoke_release,
    allowed_actors=(WorkflowActors.CLIENT, WorkflowActors.AUDITOR),
)


@mock_transition
def request_correction(self):
    pass


RequestCorrection = WorkflowTransition(
    name='request_correction',
    sources=(FinalFeedback,),
    target=CorrectionRequested,
    implementation=request_correction,
    allowed_actors=(WorkflowActors.CLIENT, WorkflowActors.AUDITOR),
)


@mock_transition
def release_auto_qa_results(self):
    pass


ReleaseAQAResults = WorkflowTransition(
    name='release_auto_qa_results',
    sources=(FinalFeedback,),
    target=AQAResultsReleased,
    implementation=release_auto_qa_results,
    allowed_actors=(WorkflowActors.CLIENT, WorkflowActors.AUDITOR),
)


@mock_transition
def technically_accept(self):
    pass


TechnicallyAccept = WorkflowTransition(
    name='technically_accept',
    sources=(AQAResultsReleased,),
    target=TechnicallyAccepted,
    implementation=technically_accept,
)


@mock_transition
def complete(self):
    pass


Complete = WorkflowTransition(
    name='complete',
    sources=(CorrectionRequested, TechnicallyAccepted),
    target=End,
    implementation=complete,
)
