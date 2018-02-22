import logging
from rest_framework import viewsets

from ...models import (
    Instrument,
    Client,
    Reporter,
    ReporterSubdivisionCategory,
    ReporterSubdivision,
    Obligation,
    ObligationSpec,
    ObligationSpecReporter,
    ReportingCycle,
)

from ...serializers import (
    InstrumentSerializer,
    ClientSerializer,
    ReporterSerializer,
    ReporterSubdivisionCategorySerializer,
    ReporterSubdivisionSerializer,
    ObligationSerializer,
    NestedObligationSpecSerializer,
    ObligationSpecReporterSerializer,
    ReportingCycleSerializer,
)

from ... import permissions


from .base import DefaultPagination
from .mixins import ReadOnlyMixin, TimeSlicedMixin

log = logging.getLogger('reportek')
info = log.info
debug = log.debug
warn = log.warning
error = log.error


__all__ = [
    'InstrumentViewSet',
    'ClientViewSet',
    'ReporterViewSet',
    'ReporterSubdivisionCategoryViewSet',
    'ReporterSubdivisionViewSet',
    'ObligationViewSet',
    'ObligationSpecViewSet',
    'ObligationSpecReporterViewSet',
    'ReportingCycleViewSet',
]


class RODMixin(ReadOnlyMixin, TimeSlicedMixin):
    permission_classes = (permissions.IsAuthenticated, )
    pagination_class = DefaultPagination


class InstrumentViewSet(RODMixin, viewsets.ModelViewSet):
    queryset = Instrument.objects.all()
    serializer_class = InstrumentSerializer


class ClientViewSet(RODMixin, viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer


class ReporterViewSet(RODMixin, viewsets.ModelViewSet):
    queryset = Reporter.objects.all()
    serializer_class = ReporterSerializer


class ReporterSubdivisionCategoryViewSet(RODMixin, viewsets.ModelViewSet):
    queryset = ReporterSubdivisionCategory.objects.all()
    serializer_class = ReporterSubdivisionCategorySerializer


class ReporterSubdivisionViewSet(RODMixin, viewsets.ModelViewSet):
    queryset = ReporterSubdivision.objects.all()
    serializer_class = ReporterSubdivisionSerializer

    def get_queryset(self):
        return super().get_queryset().filter(
            category_id=self.kwargs['category_pk']
        )


class ObligationViewSet(RODMixin, viewsets.ModelViewSet):
    queryset = Obligation.objects.all().prefetch_related('specs')
    serializer_class = ObligationSerializer


class ObligationSpecViewSet(RODMixin, viewsets.ModelViewSet):
    queryset = ObligationSpec.objects.all()
    serializer_class = NestedObligationSpecSerializer

    def get_queryset(self):
        return super().get_queryset().filter(
            obligation_id=self.kwargs['obligation_pk']
        )


class ObligationSpecReporterViewSet(RODMixin, viewsets.ModelViewSet):
    queryset = ObligationSpecReporter.objects.all()
    serializer_class = ObligationSpecReporterSerializer


class ReportingCycleViewSet(RODMixin, viewsets.ModelViewSet):
    queryset = ReportingCycle.objects.all()
    serializer_class = ReportingCycleSerializer
