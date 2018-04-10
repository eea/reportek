import logging
import xworkflows as xwf

from reportek.core.consumers.envelope import EnvelopeEvents


__all__ = []

log = logging.getLogger('reportek.workflows')
info = log.info
debug = log.debug
warn = log.warning
error = log.error


class DeleteAutoQAFeedbackMixin:

    @xwf.transition()
    def delete_auto_qa_feedback(self):
        self.bearer.envelope.  file.qa_jobs.all().delete()
        info(f'Sending envelope "{self.bearer.envelope.name}" to QA ...')
        qa_jobs_count = len(self.bearer.submit_xml_to_qa())
        info(
            f'QA started {qa_jobs_count} job(s) for envelope "{self.bearer.envelope.name}"'
        )
