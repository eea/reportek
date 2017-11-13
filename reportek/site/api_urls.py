from rest_framework import routers

from reportek.core.urls import (
    router as core_router,
    nested_routers as core_nested_routers,
)


class DefaultRouter(routers.DefaultRouter):
    """
    A `DefaultRouter` that can be extended with other routers' routes.
    NOTE: the other routers must be `SimpleRouter` instances.
    """
    def extend(self, router):
        self.registry.extend(router.registry)


root = DefaultRouter()
root.extend(core_router)

urlpatterns = root.urls + [
    url
    for routers in [core_nested_routers]
    for router in routers
    for url in router.urls
]
