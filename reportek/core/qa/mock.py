import threading

from random import random
from uuid import uuid4


class QAManagerMock:
    """
    Simulates calling QA and receving a response
    """
    def __init__(self):
        self.requests = {}

    def send(self, report, response_handler):
        request_id = uuid4()
        self.requests[request_id] = (report, response_handler)
        print(f'[QA RPC] Sending report "{report.name}" to QA [id={request_id}] ...')
        # Fake a variable time response
        t = threading.Timer(
            interval=(random() * 1.5),
            function=self.get_response,
            args=(request_id,)
        )
        t.start()
        return request_id

    def get_response(self, request_id):
        """
        Mocks a response with 50% chances of success.
        """
        response = {
            'id': request_id,
            'valid': random() >= .5
        }
        print(f'[QA RPC] Received QA response [id={request_id}]: '
              f'{"VALID" if response["valid"] else "INVALID"}')
        handler = self.requests.pop(request_id)[1]
        handler(response)
