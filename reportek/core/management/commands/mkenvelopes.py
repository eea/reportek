import os
import random
from copy import deepcopy
from datetime import date, timedelta
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.core.files.base import ContentFile
from django.contrib.postgres.aggregates import ArrayAgg
from edw.djutils.management import ProgressMixin

from reportek.core.models import (
    Envelope, EnvelopeFile,
    Obligation, ReportingPeriod,
)


DEFAULT_ENVELOPES = 100
DEFAULT_FILES = 10
DEFAULT_MIN_SIZE = 1024
DEFAULT_MAX_SIZE = 1024 * 1024


class Command(ProgressMixin, BaseCommand):
    help = (
        "Generate envelopes with files attached."
        " WARNING: will make a mess of the database."
    )

    PROGRESS_PREFIX = "Generating envelopes: "

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('envelopes', type=int,
                            nargs='?', default=DEFAULT_ENVELOPES,
                            metavar='num-envelopes',
                            help=(
                                "number of envelopes to be generated"
                                " (default %s)" % DEFAULT_ENVELOPES
                            ))
        parser.add_argument('files', type=int,
                            nargs='?', default=10,
                            metavar='num-files',
                            help=(
                                "number of files per envelope"
                                " (default %s)" % DEFAULT_FILES
                            ))

        parser.add_argument('--min-file-size', type=int,
                            default=DEFAULT_MIN_SIZE,
                            dest='min_size', metavar='BYTES',
                            help=(
                                "minimum file size in bytes"
                                " (default %s)" % DEFAULT_MIN_SIZE
                            ))

        parser.add_argument('--max-file-size', type=int,
                            default=DEFAULT_MAX_SIZE,
                            dest='max_size', metavar='BYTES',
                            help=(
                                "maximum file size in bytes"
                                " (default %s)" % DEFAULT_MAX_SIZE
                            ))

    def handle(self,
               envelopes=DEFAULT_ENVELOPES, files=DEFAULT_FILES,
               min_size=DEFAULT_MIN_SIZE, max_size=DEFAULT_MAX_SIZE,
               **options):
        ogroups = {
            row['group']: {'countries': list(set(row['countries']))}
            for row in (
                Obligation.objects
                .filter(group__workflow_class__isnull=False)
                .values('group')
                .annotate(countries=ArrayAgg('delivery_countries'))
            )
        }

        def mkranges():
            end = date.today().replace(day=1) - timedelta(days=1)
            while True:
                # make it a standard 3 months
                start = (end - timedelta(3 * 29)).replace(day=1)
                yield [start, end]
                end = start - timedelta(days=1)

        ranges = mkranges()
        period, prange = None, None
        groups = {}

        for i in range(envelopes):
            # pick each time a different combination of ogroup / country.
            # when done start anew with another period.
            if not groups:
                groups = deepcopy(ogroups)
                prange = next(ranges)

                for group in groups:
                    try:
                        period = ReportingPeriod.objects.current().get(
                            obligation_group_id=group)
                    except ObjectDoesNotExist:
                        period = ReportingPeriod.objects.create(
                            obligation_group_id=group,
                            period=prange)

                    groups[group]['period'] = period

            group = random.choice(list(groups.keys()))
            countries = groups[group]['countries']
            cidx = random.randrange(len(countries))
            country = countries.pop(cidx)

            e = Envelope.objects.create(
                name="Envelope %s" % i,
                slug="e-%s" %i,
                country_id=country,
                obligation_group_id=group,
            )

            for j in range(files):
                EnvelopeFile.objects.create(
                    envelope_id=e.id,
                    file=ContentFile(
                        os.urandom(
                            random.randint(min_size, max_size)
                        ),
                        name='f-%s' % j
                    ),
                )

            if not countries:
                groups[group]['period'].close()
                del groups[group]

            self.progress(i + 1, envelopes)
