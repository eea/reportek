"""
This package handles RPC calls with QA
"""

# Only a mock is implemented for now
from .mock import QAConnectionMock as QAConnection
from .xml_rpc import RemoteQA
