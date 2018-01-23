from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^envelopes/(?P<pk>[0-9]+)/$',
        views.EnvelopeView.as_view(),
        name='envelope'),
    url(r'^envelopes/(?P<pk>[0-9]+)/xml$',
        views.EnvelopeMetadataView.as_view(),
        name='envelope-metadata'),
    url(r'^envelopes/(?P<pk>[0-9]+)/(?P<filename>[^/]+)$',
        views.EnvelopeFileDownloadView.as_view(),
        name='envelope-file'),
]
