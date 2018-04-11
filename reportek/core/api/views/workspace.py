from .mixins import PendingObligationsMixin

import logging
from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from ...models import (
    Envelope,
)

from ...serializers import (
    ReporterSerializer,
    PendingObligationSerializer,
    WorkspaceEnvelopeSerializer,
    WorkspaceUserSerializer,
)


log = logging.getLogger('reportek')
info = log.info
debug = log.debug
warn = log.warning
error = log.error


__all__ = [
    'WorkspaceProfileViewSet',
    'WorkspaceReporterViewSet',
]


class WorkspaceProfileViewSet(viewsets.ViewSet):
    """
    Viewset for the user's workspace profile.

    list:
    User details of use in workspace:
     - userfirst/last names, email
     - group memberships (Django, LDAP and effective)
     - `Reporters` for which they can report.
    """
    def list(self, request):
        serializer = WorkspaceUserSerializer(request.user)
        return Response(serializer.data)


class WorkspaceReporterViewSet(PendingObligationsMixin,
                               viewsets.ReadOnlyModelViewSet):
    """
    list:
    Lists the `Reporter`s for which the user can report, and the detail views:

    wip:
    Lists envelopes in progress.

    archive:
    Lists archived (finalized) envelopes.

    pending:
    Lists pending obligations.
    """

    serializer_class = ReporterSerializer

    def get_queryset(self):
        return self.request.user.get_reporters()

    @staticmethod
    def get_envelopes(user, reporter, finalized=False, serialize=True):
        envelopes = Envelope.objects.filter(
            assigned_to=user,
            reporter=reporter,
            finalized=finalized
        )
        if serialize:
            envelopes = WorkspaceEnvelopeSerializer(envelopes, many=True).data
        return envelopes

    @detail_route()
    def wip(self, request, pk):
        reporter = self.get_object()
        envelopes = self.get_envelopes(request.user, reporter, finalized=False)
        return Response(envelopes)

    @detail_route()
    def archive(self, request, pk):
        reporter = self.get_object()
        envelopes = self.get_envelopes(request.user, reporter, finalized=True)
        return Response(envelopes)

    @detail_route()
    def pending(self, request, pk):
        reporter = self.get_object()
        obligations = self.pending_obligations(request, reporter, user_only=True)
        serializer = PendingObligationSerializer(
            obligations.values(), many=True, context={'request': request})
        return Response(serializer.data)
