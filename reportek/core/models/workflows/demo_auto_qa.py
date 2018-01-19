import logging
import xworkflows as xwf

from .base import BaseWorkflow
from reportek.core.qa import QAConnection

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

    qa_conn = QAConnection(min_delay=1)

    class Meta:
        verbose_name = 'Workflow - Auto QA'
        verbose_name_plural = 'Workflows - Auto QA '

    @xwf.transition()
    def send_to_qa(self):
        info('Sending to QA ...')
        request_id = self.bearer.submit_to_qa()
        info(f'QA submission successful (request id {request_id})')

    def handle_qa_result(self, result):
        """
        Example of QA callback with automatic transition logic.
        """
        trans_name = 'pass_qa' if result['valid'] else 'fail_qa'
        trans_meth = getattr(self.xwf, trans_name)
        info(f'Automatic transition "{trans_name}" '
             f'triggered by QA response [id={result["id"]}]: '
             f'{"VALID" if result["valid"] else "INVALID"}')
        import time
        while self.current_state != 'auto_qa':
            info('Waiting for state to become auto_qa ...')
            time.sleep(1)
        trans_meth()

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
        info('Automatic transition "fail_qa" triggered by QA response: "INVALID"')
        self.fail_qa()


class DemoPassQAWorkflow(DemoAutoQAWorkflow):

    @xwf.transition()
    def send_to_qa(self):
        info('Sending to QA ...')
        info(f'QA submission successful')

    @xwf.on_enter_state('auto_qa')
    def hook_on_enter(self, *args, **kwargs):
        info('Automatic transition "pass_qa" triggered by QA response: "VALID"')
        self.pass_qa()
