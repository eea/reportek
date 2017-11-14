from rest_framework_nested import routers

from .views import (
    EnvelopeViewSet,
    EnvelopeFileViewSet,
    EnvelopeWorkflowViewSet,
)


router = routers.SimpleRouter()
router.register(
    'envelopes',
    EnvelopeViewSet,
    base_name='envelope'
)

files_router = routers.NestedSimpleRouter(
    router, 'envelopes', lookup='envelope')
files_router.register(
    'files',
    EnvelopeFileViewSet,
    base_name='envelope-file'
)

workflow_router = routers.NestedSimpleRouter(
    router, 'envelopes', lookup='envelope')
workflow_router.register(
    'workflow',
    EnvelopeWorkflowViewSet,
    base_name='envelope-workflow'
)

nested_routers = [
    files_router,
    workflow_router
]
