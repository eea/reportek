
class ReportekWorkflowError(Exception):
    pass


class MisconfiguredWorkflowError(ReportekWorkflowError):
    pass


class TransitionDoesNotExistError(ReportekWorkflowError):
    pass


class TransitionNotAvailableError(ReportekWorkflowError):
    pass


class StateDoesNotExistError(ReportekWorkflowError):
    pass
