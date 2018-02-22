import dateutil.parser
import logging
from django.db.models import Q, Exists, OuterRef
from rest_framework import viewsets

from ...models import (
    ReporterSubdivisionCategory,
    ReportingCycle,
    Envelope,
)

from ... import permissions

from .base import DefaultPagination


log = logging.getLogger('reportek.workflows')
info = log.info
debug = log.debug
warn = log.warning
error = log.error


class ReadOnlyMixin:
    def _allowed_methods(self):
        return ['GET', 'OPTIONS']


class TimeSlicedMixin:
    """
    Provides a time-sliced query set, based on the URL query parameters
    `since` and/or `until`. The parameters must be ISO 8601 date-time strings,
    e.g. '2007-04-05T14:30Z' or '2007-04-05T16:30+02:00'.
    """
    def get_queryset(
        self  # type:  viewsets.ModelViewSet
    ):
        """
        Filters the query set based on the `updated_at`/`created_at` fields.
        """
        query_params = self.request.query_params
        queryset = super().get_queryset()
        try:
            since = dateutil.parser.parse(query_params['since'])
        except KeyError:
            since = None

        q_since = Q(updated_at__gt=since) | (Q(updated_at=None) & Q(created_at__gt=since))

        try:
            until = dateutil.parser.parse(query_params['until'])
        except KeyError:
            until = None

        q_until = Q(updated_at__lt=until) | (Q(updated_at=None) & Q(created_at__lt=until))

        if since is not None:
            q = q_since
            if until is not None:
                q &= q_until
        elif until is not None:
            q = q_until
        else:
            return queryset

        return queryset.filter(q)

    def paginate_queryset(
        self,  # type:  viewsets.ModelViewSet
        queryset
    ):
        """
        Overrides default paginator to disable it when time slice params are present.
        """
        query_params = self.request.query_params
        if self.paginator is None or 'since' in query_params or 'until' in query_params:
            return None
        return self.paginator.paginate_queryset(queryset, self.request, view=self)


class RODMixin(ReadOnlyMixin, TimeSlicedMixin):
    permission_classes = (permissions.IsAuthenticated, )
    pagination_class = DefaultPagination


class PendingObligationsMixin:

    @staticmethod
    def pending_obligations(request, reporter, user_only=False):
        """
        Returns obligations with open reporting cycles for obligation specs
        that have no envelopes from the reporter, or have continuous reporting.

        Relevant data on reporting cycles and applicable reporter subdivisions
        is custom serialized within each obligation.
        """

        envelopes = Envelope.objects.filter(
            reporter=reporter,
            reporting_cycle=OuterRef('pk')
        )
        reporting_cycles = ReportingCycle.objects.for_reporter(reporter, open_only=True).\
            annotate(has_envelopes=Exists(envelopes)).filter(
            Q(has_envelopes=False) | Q(reporting_end_date__isnull=True)
        )

        obligation_specs = reporter.obligation_specs.filter(
            reporting_cycles__in=reporting_cycles)

        if user_only:
            user_obligations = request.user.get_obligations()
            obligations = {
                spec.obligation_id: spec.obligation
                for spec in obligation_specs
                if spec and spec.obligation in user_obligations
            }
        else:
            obligations = {
                spec.obligation_id: spec.obligation
                for spec in obligation_specs
                if spec
            }

        subdivision_category_ids = set(
            rep_cycle.subdivision_category for rep_cycle in reporting_cycles
        )

        subdivision_categories = {
            cat.id: cat
            for cat in
            ReporterSubdivisionCategory.objects.filter(
                id__in=subdivision_category_ids
            ).prefetch_related('subdivisions')
        }

        for rep_cycle in reporting_cycles:
            oblig = obligations[rep_cycle.obligation_spec.obligation_id]

            try:
                rep_cycle.subdivisions = subdivision_categories[rep_cycle.subdivision_category].subdivisions.all()
            except KeyError:
                rep_cycle.subdivisions = []

            try:
                oblig.reporting_cycles.append(rep_cycle)
            except AttributeError:
                oblig.reporting_cycles = [rep_cycle]

        return obligations
