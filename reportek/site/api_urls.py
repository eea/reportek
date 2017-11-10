from rest_framework import routers

from reportek.core.urls import router as core_router


class DefaultRouter(routers.DefaultRouter):
    """
    A `DefaultRouter` that can be extended with other routers' routes.
    NOTE: the other routers must be `SimpleRouter` instances.
    """
    def extend(self, router):
        self.registry.extend(router.registry)


router = DefaultRouter()
router.extend(core_router)

urlpatterns = router.urls
