import logging
import xworkflows as xwf

from reportek.core.consumers.envelope import EnvelopeEvents

from .base import BaseWorkflow

__all__ = [
    'DemoAutoQAWorkflow',
    'DemoFailQAWorkflow',
    'DemoPassQAWorkflow'
]

log = logging.getLogger('reportek.workflows')
info = log.info
debug = log.debug
warn = log.warning
error = log.error


class DemoAutoQAWorkflow(BaseWorkflow):

    states = (
        ('draft', 'Draft'),
        ('auto_qa', 'Auto QA'),
        ('review', 'Review'),
        ('released', 'Released')
    )
    transitions = (
        ('send_to_qa', 'draft', 'auto_qa'),
        ('fail_qa', 'auto_qa', 'draft'),
        ('pass_qa', 'auto_qa', 'review'),
        ('reject', 'review', 'draft'),
        ('release', 'review', 'released')
    )
    initial_state = 'draft'
    final_state = 'released'
    upload_states = ['draft']

    class Meta:
        verbose_name = 'Workflow - Auto QA'
        verbose_name_plural = 'Workflows - Auto QA '

    @xwf.transition()
    def send_to_qa(self):
        info(f'Sending envelope "{self.bearer.envelope.name}" to QA ...')
        qa_jobs_count = len(self.bearer.submit_xml_to_qa())
        info(f'QA started {qa_jobs_count} job(s) for envelope "{self.bearer.envelope.name}"')

    @xwf.on_enter_state('auto_qa')
    def on_enter_auto_qa(self, *args, **kwargs):
        if len(self.bearer.envelope.auto_qa_jobs) == 0:
            info('No QA jobs found on entering auto_qa state')
            self.pass_qa()

    def handle_auto_qa_results(self):
        """
        Example of QA callback with automatic transition logic.
        """
        if self.current_state != 'auto_qa':
            warn('Cannot handle Auto QA results - envelope is not in "Auto QA" state!')
            return

        if not self.envelope.auto_qa_complete:
            info('Skipping Auto QA results handling - not all jobs have completed.')
            self.announce_auto_qa_status(EnvelopeEvents.RECEIVED_AUTO_QA_FEEDBACK)
            return

        self.announce_auto_qa_status(EnvelopeEvents.COMPLETED_AUTO_QA)
        trans_name = 'pass_qa' if self.envelope.auto_qa_ok else 'fail_qa'
        trans_meth = getattr(self.xwf, trans_name)
        info(f'Automatic transition "{trans_name}" triggered by Auto QA response(s)')
        return trans_meth()

    @xwf.transition()
    def fail_qa(self):
        info('"fail_qa" running')

    @xwf.transition()
    def pass_qa(self):
        info('"pass_qa" running')

    @xwf.transition()
    def reject(self):
        info('"reject" running')

    @xwf.transition()
    def release(self):
        info('"release" running')


class DemoFailQAWorkflow(DemoAutoQAWorkflow):

    @xwf.transition()
    def send_to_qa(self):
        info('Sending to QA ...')
        info(f'QA submission successful')

    @xwf.on_enter_state('auto_qa')
    def hook_on_enter(self, *args, **kwargs):
        info('Automatic transition "fail_qa" triggered by Auto QA response(s)')
        self.fail_qa()


class DemoPassQAWorkflow(DemoAutoQAWorkflow):

    @xwf.transition()
    def send_to_qa(self):
        info('Sending to QA ...')
        info(f'QA submission successful')

    @xwf.on_enter_state('auto_qa')
    def hook_on_enter(self, *args, **kwargs):
        info('Automatic transition "pass_qa" triggered by Auto QA response(s)')
        self.pass_qa()
