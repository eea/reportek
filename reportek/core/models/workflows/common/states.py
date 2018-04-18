from ..base import WorkflowState

__all__ = [
    'Draft',
    'AQAResultsDeleted',
    'AQAPending',
    'AQAPassed',
    'AQAFailed',
    'CRPinged',
    'AQAResultsRestricted',
    'ReceiptConfirmed',
    'Released',
    'FinalFeedback',
    'ReleaseRevoked',
    'AQARerunRequested',
    'CorrectionRequested',
    'TechnicallyAccepted',
    'AQAResultsReleased',
    'End',
]

# Actual reporting takes place during this state
Draft = WorkflowState(name='draft', title='Draft')

AQAResultsDeleted = WorkflowState(name='qa_results_deleted', title='Auto QA Results Deleted')

AQAPending = WorkflowState(name='qa_pending', title='AQA Pending')

AQAPassed = WorkflowState(name='qa_passed', title='AQA Passed')

AQAFailed = WorkflowState(name='qa_failed', title='AQA Failed')

CRPinged = WorkflowState(name='cr_pinged', title='CR Pinged')

AQAResultsRestricted = WorkflowState(name='qa_results_restricted', title='Auto QA Results Restricted')

ReceiptConfirmed = WorkflowState(name='receipt_confirmed', title='Receipt Confirmed')

Released = WorkflowState(name='released', title='Released')

# State during which the decision to accept or reject the envelope is taken
FinalFeedback = WorkflowState(name='final_feedback', title='Final Feedback')

ReleaseRevoked = WorkflowState(name='release_revoked', title='Release Revoked')

# This state indicates that a QA re-run was initiated
AQARerunRequested = WorkflowState(name='qa_rerun_requested', title='Auto QA Rerun Requested')

CorrectionRequested = WorkflowState(name='correction_requested', title='Correction Requested')

TechnicallyAccepted = WorkflowState(name='technically_accepted', title='Technically Accepted')

AQAResultsReleased = WorkflowState(name='qa_results_released', title='Auto QA Results Released')

# The cannonical final state of all envelopes
End = WorkflowState(name='end', title='End')
