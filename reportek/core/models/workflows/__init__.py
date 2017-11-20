"""
Workflow models - common functionality and specific implementations.
"""
from .base import BaseWorkflow
from .log import TransitionEvent

from .base import BaseWorkflow
from .demo_auto_qa import DemoAutoQAWorkflow

from reportek.core.utils import get_based_classes


WORKFLOW_CLASSES = get_based_classes(__path__, __package__, 'BaseWorkflow')
