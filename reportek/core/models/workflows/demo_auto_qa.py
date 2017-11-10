import xworkflows as xwf

from .base import BaseWorkflow

__all__ = [
    'DemoAutoQA',
]


class DemoAutoQAWorkflow(BaseWorkflow):

    states = (
        ('draft', 'Draft'),
        ('auto_qa', 'Auto QA'),
        ('review', 'Review'),
        ('end', 'End')
    )
    transitions = (
        ('send_to_qa', 'draft', 'auto_qa'),
        ('fail_qa', 'auto_qa', 'draft'),
        ('pass_qa', 'auto_qa', 'review'),
        ('reject', 'review', 'draft'),
        ('accept', 'review', 'end')
    )
    initial_state = 'draft'

    class Meta:
        verbose_name = 'Workflow - Auto QA'
        verbose_name_plural = 'Workflows - Auto QA '

    @xwf.transition()
    def send_to_qa(self):
        print('Sending to QA ...')
        request_id = self.bearer.submit_to_qa()
        print(f'QA submission successful (request id {request_id})')

    def handle_qa_result(self, result):
        """
        Example of QA callback with automatic transition logic.
        """
        trans_name = 'pass_qa' if result['valid'] else 'fail_qa'
        trans_meth = getattr(self.xwf, trans_name)
        print(f'Automatic transition "{trans_name}" '
              f'triggered by QA response [id={result["id"]}]: '
              f'{"VALID" if result["valid"] else "INVALID"}')
        import time
        while self.current_state != 'auto_qa':
            print('Waiting for state to become auto_qa ...')
            time.sleep(1)
        trans_meth()

    @xwf.transition()
    def fail_qa(self):
        print('"fail_qa" running')

    @xwf.transition()
    def pass_qa(self):
        print('"pass_qa" running')

    @xwf.transition()
    def reject(self):
        print('"reject" running')

    @xwf.transition()
    def accept(self):
        print('"accept" running')
