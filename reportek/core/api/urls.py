# normally this shouldn't be used, as all routers will be wrapped together
# in the final set of API urls
from .routers import (
    envelopes_router,
    nested_envelopes_routers,
    uploads_router,
)


urlpatterns = uploads_router.urls + envelopes_router.urls + [
    url
    for r in nested_envelopes_routers
    for url in r.urls
]
