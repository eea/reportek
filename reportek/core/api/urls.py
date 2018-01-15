from rest_framework import routers

from reportek.core.api.routers import (
    main_routers,
    nested_routers
)


class DefaultRouter(routers.DefaultRouter):
    """
    A `DefaultRouter` that can be extended with other routers' routes.
    NOTE: the other routers must be `SimpleRouter` instances.
    """
    def extend(self, router):
        self.registry.extend(router.registry)


root = DefaultRouter()

for router in main_routers:
    root.extend(router)

urlpatterns = root.urls + \
              [
                  url
                  # for nested_router in nested_routers
                  for router in nested_routers
                  for url in router.urls
              ]
