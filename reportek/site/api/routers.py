from rest_framework.routers import DefaultRouter

from .views import (
    ReporterPendingObligations,
    ReporterOpenEnvelopes,
    ReporterClosedEnvelopes,
)


my_router = DefaultRouter()

my_router.register(
    'pending-obligations',
    ReporterPendingObligations,
    base_name='pending-obligation',
)
my_router.register(
    'open-envelopes',
    ReporterOpenEnvelopes,
    base_name='open-envelope',
)
my_router.register(
    'closed-envelopes',
    ReporterClosedEnvelopes,
    base_name='closed-envelope',
)
