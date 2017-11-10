from django.conf.urls import url
from rest_framework import routers

from .views import EnvelopeViewSet


router = routers.SimpleRouter()
router.register('envelopes', EnvelopeViewSet, base_name='envelope')

urlpatterns = router.urls
