from rest_framework_nested import routers

from .views import (
    EnvelopeViewSet,
    EnvelopeFileViewSet,
    EnvelopeWorkflowViewSet,
    UploadHookView,
    UploadTokenViewSet,
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


upload_token_router = routers.NestedSimpleRouter(
    envelopes_router, 'envelopes', lookup='envelope')
upload_token_router.register(
    'token',
    UploadTokenViewSet,
    base_name='envelope-token'
)

nested_envelopes_routers = [
    files_router,
    workflow_router,
    upload_token_router,
]


upload_hooks_router = routers.SimpleRouter()
upload_hooks_router.register(
    'uploads',
    UploadHookView,
    base_name='uploads'
)
