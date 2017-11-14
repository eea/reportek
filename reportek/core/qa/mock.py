import logging
import threading
from random import random
from uuid import uuid4

log = logging.getLogger('reportek.qa')
info = log.info
debug = log.debug
warn = log.warning
error = log.error


class QAConnectionMock:
    """
    Simulates calling QA and receving a response
    """
    def __init__(self):
        self.requests = {}  # Maps request ids to response handlers

    def send(self, envelope, response_handler):
        request_id = uuid4()
        self.requests[request_id] = response_handler
        info(f'[QA RPC] Sending envelope "{envelope.name}" to QA [id={request_id}] ...')
        # Fake a variable time response
        t = threading.Timer(
            interval=(1 + random() * 1.5),
            function=self.get_response,
            args=(request_id,)
        )
        t.start()
        return request_id

    def get_response(self, request_id):
        """
        Mocks a response with 50% chances of success.
        """
        # time.sleep((1 + random() * 1.5))
        response = {
            'id': request_id,
            'valid': random() >= .5
        }
        info(f'[QA RPC] Received QA response for request id "{request_id}": '
             f'{"VALID" if response["valid"] else "INVALID"}')
        handler = self.requests.pop(request_id)
        handler(response)
