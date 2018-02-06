from collections import OrderedDict
from django.db.models import F
from rest_framework.generics import ListAPIView
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin

from reportek.core.models import (
    ReportingCycle, ReporterSubdivisionCategory,
)
from .permissions import IsReporter
from .serializers import ObligationSerializer


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
    # TODO: !!
    # - excluding those that already have an envelope created,
    #   unless they're continuous-reporting

    permission_classes = (IsReporter,)
    serializer_class = ObligationSerializer
    # (this is entirely custom, make sure it doesn't get filtered / paginated)
    filter_backends = []
    pagination_class = None


    def get_queryset(self):
        reporter = self.request.user.reporter

        # it's the cycles and subdivisions we're really after,
        # but we're gonna make this look like an obligations query
        cycles = ReportingCycle.objects.open().filter(
            obligation_spec__reporter_mapping__reporter=reporter,
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


class ReporterOpenEnvelopes(_ListViewSet):
    pass


class ReporterClosedEnvelopes(_ListViewSet):
    pass
