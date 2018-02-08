from collections import OrderedDict
from django.db.models import F, Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import (
    ListModelMixin,
    CreateModelMixin,
)
from rest_framework.response import Response

from reportek.core.models import (
    ReportingCycle, ReporterSubdivisionCategory,
    Envelope,
)
from .permissions import (
    IsSiteUser, IsReporter,
)
from .serializers import (
    UserSerializer, ReporterUserSerializer,
    PendingObligationSerializer,
    EnvelopeSerializer, CreateEnvelopeSerializer,
)


# this one's too simple to warrant a view
@api_view()
@permission_classes((IsSiteUser,))
def user_profile(request):
    serializer = (
        ReporterUserSerializer if request.user.is_reporter()
        else UserSerializer
    )
    return Response(
        serializer(request.user).data
    )


# setting things up as viewsets so we can have pretty routes and index view
class _ListViewSet(ListModelMixin, GenericViewSet):
    pass


class ReporterPendingObligations(_ListViewSet):
    """
    Returns a list of all obligations that the current reporter
    needs to submit an envelope for.
    """
    # that means:
    # - obligations whose current spec includes the current user as reporter,
    # - that have a currently open reporting cycle,
    # - excluding those that already have an envelope created,
    #   unless they're continuous-reporting
    # TODO: (?!) or the envelope is open?

    permission_classes = (IsReporter,)
    serializer_class = PendingObligationSerializer
    # (this is entirely custom, make sure it doesn't get filtered / paginated)
    filter_backends = []
    pagination_class = None

    def get_queryset(self):
        reporter = self.request.user.reporter

        # it's the cycles and subdivisions we're really after,
        # but we're gonna make this look like an obligations query
        cycles = ReportingCycle.objects.open().for_reporter(
            reporter
        ).exclude(
            Q(reporting_end_date__isnull=False) &
            Q(pk__in=reporter.envelopes.all().values('reporting_cycle'))
        ).select_related(
            'obligation_spec',
            'obligation_spec__obligation',
            'obligation_spec__obligation__instrument',
            'obligation_spec__obligation__client',
        ).annotate(
            _catid=F('obligation_spec__reporter_mapping__subdivision_category')
        ).order_by(
            '-reporting_start_date',
        )

        # prefetch the subdivisions
        _categories = ReporterSubdivisionCategory.objects.filter(
            id__in=set(c._catid
                       for c in cycles
                       if c._catid is not None)
        ).prefetch_related('subdivisions')

        categories = {
            c.id: c
            for c in _categories
        }

        # regroup by obligation
        obligations = OrderedDict()
        for cycle in cycles:
            o = cycle.obligation_spec.obligation
            try:
                obligation = obligations[o.id]
            except KeyError:
                obligation = obligations[o.id] = o
                obligation.cycles = []

            # glue the subdivisions to the cycle
            if cycle._catid is not None:
                cycle.subdivisions = categories[cycle._catid].subdivisions.all()
            else:
                cycle.subdivisions = ()

            obligation.cycles.append(cycle)

        return obligations.values()


class _BaseReporterEnvelopes(_ListViewSet):
    permission_classes = (IsReporter,)
    serializer_class = EnvelopeSerializer

    def get_queryset(self):
        reporter = self.request.user.reporter

        envelopes = Envelope.objects.filter(
            reporter=reporter
        ).select_related(
            'reporter_subdivision',
            'reporting_cycle',
            'reporting_cycle__obligation_spec',
            'reporting_cycle__obligation_spec__obligation',
            'reporting_cycle__obligation_spec__obligation__instrument',
            'reporting_cycle__obligation_spec__obligation__client',
        )

        return envelopes


class ReporterOpenEnvelopes(CreateModelMixin, _BaseReporterEnvelopes):
    def get_queryset(self):
        envelopes = super().get_queryset()
        return envelopes.open()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateEnvelopeSerializer

        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user.reporter)


class ReporterClosedEnvelopes(_BaseReporterEnvelopes):
    def get_queryset(self):
        envelopes = super().get_queryset()
        return envelopes.closed()
