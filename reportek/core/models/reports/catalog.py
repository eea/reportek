import xworkflows as xwf

from .base import BaseReport
from .base import WFState


class FinishMixin:
    @xwf.transition()
    def finish(self):
        end_state = WFState.objects.get(name='end', workflow=self.report.workflow)
        self.report.wf_state = end_state
        self.report.save()
        print(f'{self.report.name} is finished!!!')


class ReportOne(BaseReport, FinishMixin):
    class Meta:
        verbose_name = 'report'
