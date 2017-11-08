from functools import wraps
import xworkflows as xwf

from .base import BaseReport
from .base import WFState

__all__ = [
    'ReportSimple',
]


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
            next_state = WFState.objects.get(
                name=to_state,
                workflow=self.report.workflow)
            self.report.wf_state = next_state
            self.report.save()
            print(f'{self.report.name} is now in state {next_state.name}!!!')
        return wrapper
    return decorator


class FinishMixin:
    @xwf.transition()
    @dumb_transition('end')
    def finish(self):
        pass


class ReportSimple(BaseReport, FinishMixin):
    class Meta:
        verbose_name = 'report (simple)'
        verbose_name_plural = 'reports (simple)'
