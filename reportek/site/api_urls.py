from rest_framework import routers

from reportek.core.api.routers import (
    router as core_router,
    nested_routers as core_nested_routers,
)


main_routers = [core_router]
nested_routers_set = [core_nested_routers]


class DefaultRouter(routers.DefaultRouter):
    """
    A `DefaultRouter` that can be extended with other routers' routes.
    NOTE: the other routers must be `SimpleRouter` instances.
    """
    def extend(self, router):
        self.registry.extend(router.registry)


root = DefaultRouter()
for router in main_routers:
    root.extend(core_router)


urlpatterns = root.urls + [
    url
    for routers in nested_routers_set
    for router in routers
    for url in router.urls
]
