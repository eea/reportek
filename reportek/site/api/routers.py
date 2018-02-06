from rest_framework.routers import DefaultRouter

from .views import (
    ReporterPendingObligations,
)


my_router = DefaultRouter()

my_router.register(
    'pending-obligations',
    ReporterPendingObligations,
    base_name='pending-obligation',
)
