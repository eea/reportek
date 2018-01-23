from django.core.exceptions import ObjectDoesNotExist
from django.http.response import Http404
from django.utils.functional import cached_property
from django.shortcuts import render
from edw.djutils import protected

from ..models import (
    Envelope, EnvelopeFile,
)
from .. import permissions


class EnvelopeView(protected.views.ProtectedDetailView):
    model = Envelope
    permission_classes = (permissions.IsAuthenticatedOrEnvelopeIsPublic, )
    template_name = 'envelope.html'


class EnvelopeMetadataView(protected.views.ProtectedDetailView):
    model = Envelope
    permission_classes = (permissions.IsAuthenticatedOrEnvelopeIsPublic, )
    template_name = 'envelope_xml.jinja2'

    def get(self, request, *args, **kwargs):
        envelope = self.get_object()
        return render(
            request,
            template_name=self.template_name,
            context={'envelope': envelope},
            content_type='application/xml'
        )


class EnvelopeFileDownloadView(protected.views.ProtectedBaseDetailFileView):
    model = Envelope
    permission_classes = (permissions.IsAuthenticatedOrEnvelopeIsPublic, )

    @cached_property
    def _file(self):
        envelope = self.get_object()
        try:
            efile = envelope.files.filter(
                name=self.kwargs['filename']
            ).get()
        except ObjectDoesNotExist:
            raise Http404()
        return efile.file

    def get_storage(self):
        return self._file.storage

    def get_file_path(self):
        return self._file.name
