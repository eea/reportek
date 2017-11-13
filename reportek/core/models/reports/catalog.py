from functools import wraps
import xworkflows as xwf

from reportek.core.qa import QAConnection


def dumb_transition(to_state):
    """
    Implements a generic transition with no logic except moving
    to the indicated state.
    NOTE:
        Anything in the decorated method is simply ignored.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(self, *args, **kwargs):
            prev_state = self.report.wf_state
            next_state = ''
            self.report.log_transition(f.__name__, prev_state, next_state)
            print(f'"{self.report.name}" is now in state "{next_state.name}".')
        return wrapper
    return decorator


class FinishMixin:
    @xwf.transition()
    @dumb_transition('end')
    def finish(self):
        pass


class SendToQAMixin:

    qa_mgr = QAConnection()

    @xwf.transition()
    def send_to_qa(self):
        pass

    def handle_qa_result(self, result):
        trans_name = 'qa_succeeded' if result['valid'] else 'qa_failed'
        trans_meth = getattr(self.xwf, trans_name)
        print(f'Automatic migration "{trans_name}" '
              f'triggered by QA response [id={result["id"]}]: '
              f'{"VALID" if result["valid"] else "INVALID"}')
        trans_meth()

    @xwf.transition()
    @dumb_transition('draft')
    def qa_failed(self):
        pass

    @xwf.transition()
    @dumb_transition('review')
    def qa_succeeded(self):
        pass

    @xwf.transition()
    @dumb_transition('draft')
    def reject(self):
        pass

    @xwf.transition()
    @dumb_transition('end')
    def accept(self):
        pass


class ReportSimple(FinishMixin):

    class Meta:
        verbose_name = 'report (simple)'
        verbose_name_plural = 'reports (simple)'


class ReportWithQA(SendToQAMixin):

    class Meta:
        verbose_name = 'report (with QA)'
        verbose_name_plural = 'reports (with QA)'
