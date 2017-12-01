from rest_framework_nested import routers

from .views import (
    EnvelopeViewSet,
    EnvelopeFileViewSet,
    EnvelopeWorkflowViewSet,
    UploadHookView
)


envelopes_router = routers.SimpleRouter()
envelopes_router.register(
    'envelopes',
    EnvelopeViewSet,
    base_name='envelope'
)

files_router = routers.NestedSimpleRouter(
    envelopes_router, 'envelopes', lookup='envelope')
files_router.register(
    'files',
    EnvelopeFileViewSet,
    base_name='envelope-file'
)

workflow_router = routers.NestedSimpleRouter(
    envelopes_router, 'envelopes', lookup='envelope')
workflow_router.register(
    'workflow',
    EnvelopeWorkflowViewSet,
    base_name='envelope-workflow'
)

nested_envelopes_routers = [
    files_router,
    workflow_router
]


uploads_router = routers.SimpleRouter()
uploads_router.register(
    'uploads',
    UploadHookView,
    base_name='uploads'
)
