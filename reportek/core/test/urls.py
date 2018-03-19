from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^channels/envelopes/(?P<pk>[0-9]+)/$',
        views.EnvelopeChannelTest.as_view(),
        name='envelope-channel'),
]
