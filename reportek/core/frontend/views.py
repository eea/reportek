from django.core.exceptions import ObjectDoesNotExist
from django.http.response import Http404
from django.utils.functional import cached_property
from edw.djutils import protected

from ..models import (
    Envelope, EnvelopeFile,
)
from .. import permissions


class EnvelopeView(protected.views.ProtectedDetailView):
    model = Envelope
    permission_classes = (permissions.IsAuthenticatedOrEnvelopeIsPublic, )
    template_name = 'envelope.html'


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
