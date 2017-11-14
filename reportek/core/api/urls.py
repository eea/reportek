# normally this shouldn't be used, as all routers will be wrapped together
# in the final set of API urls
from .routers import router, nested_routers


urlpatterns = router.urls + [
    url
    for r in nested_routers
    for url in r.urls
]
