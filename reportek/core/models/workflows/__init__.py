"""
Workflow models - common functionality and specific implementations.
"""
from .base import BaseWorkflow
from .log import TransitionEvent

# from .demo_auto_qa import (
#     DemoAutoQAWorkflow,
#     DemoFailQAWorkflow,
#     DemoPassQAWorkflow,
# )

from .reference import ReferenceWorkflow


WORKFLOW_CHOICES = {
    ('.'.join([k.__module__, k.__name__]), k.__name__)
    for k in BaseWorkflow.get_type_classes()
}
