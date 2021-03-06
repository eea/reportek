"""
Workflow models - common functionality and specific implementations.
"""
from .base import BaseWorkflow
from .log import TransitionEvent

from .demo_auto_qa import (
    DemoAutoQAWorkflow,
    DemoFailQAWorkflow,
    DemoPassQAWorkflow,
)

from reportek.core.utils import get_based_classes


WORKFLOW_CLASSES = get_based_classes(__path__, __package__, 'BaseWorkflow')
