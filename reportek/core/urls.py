from django.conf.urls import url
from rest_framework_nested import routers

from .views import (
    EnvelopeViewSet, EnvelopeFileViewSet,
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

nested_routers = [files_router]

urlpatterns = router.urls + [
    url
    for r in nested_routers
    for url in r.urls
]
