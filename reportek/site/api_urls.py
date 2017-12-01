from rest_framework import routers

from reportek.core.api.routers import (
    envelopes_router,
    nested_envelopes_routers,
    uploads_router
)


main_routers = [envelopes_router, uploads_router]
nested_routers = [nested_envelopes_routers]


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
              envelopes_router.urls + \
              uploads_router.urls + \
              [
                  url
                  for nested_router in nested_routers
                  for router in nested_router
                  for url in router.urls
              ]
