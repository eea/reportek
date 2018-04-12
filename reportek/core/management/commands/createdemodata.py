from django.core.management.base import BaseCommand
from django.conf import settings

from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from guardian.shortcuts import assign_perm

from reportek.core.models import (
    Obligation,
    ObligationSpec,
    ObligationSpecReporter,
    Reporter,
    ReportingCycle,
    Envelope,
    EnvelopeFile,
)


REPORTERS = (
    'AL',
    'CZ',
)

# Map of obligation codes with tuples of (obligation title, obligation group prefix)
OBLIGATIONS = {
    'WISE-3': ('WISE SoE - Water Quantity (WISE-3)', 'reportnet-awp-wise3-reporter'),
    'WISE-4': ('WISE SoE - Water Quality (WISE-4)', 'reportnet-awp-wise4-reporter')
}

OBLIGATIONS_REPORTERS_MAP = {
    'WISE-3': ('AL', 'CZ',),
    'WISE-4': ('CZ',),
}

WORKFLOW = 'reportek.core.models.workflows.demo_auto_qa.DemoAutoQAWorkflow'

REPORTING_MODELS = (
    Envelope,
    EnvelopeFile,
)


def get_reporting_model_permissions():
    """Builds list of basic permissions on reporting models"""
    perms = []
    perm_prefixes = ['add', 'change', 'delete']
    for model_cls in REPORTING_MODELS:
        model_name = model_cls.__name__.lower()
        for prefix in perm_prefixes:
            perms.append(
                Permission.objects.get(codename=f'{prefix}_{model_name}')
            )
    return perms


class Command(BaseCommand):

    help = f'Create demo data: obligation specifications, reporting cycles, groups and permissions.'

    def handle(self, **options):
        reporter_type = ContentType.objects.get(app_label='core', model='reporter')
        reporter_perm = Permission.objects.get(content_type=reporter_type, codename='report_for_reporter')

        obligation_type = ContentType.objects.get(app_label='core', model='obligation')
        oblig_perm = Permission.objects.get(content_type=obligation_type, codename='report_on_obligation')

        reporting_model_perms = get_reporting_model_permissions()

        for oblig_code, oblig_info in OBLIGATIONS.items():
            oblig_title, oblig_group_prefix = oblig_info
            try:
                oblig = Obligation.objects.get(title=oblig_title)
            except Obligation.DoesNotExist:
                print(f'ERROR: could not find obligation "{oblig_title}"')
                continue

            print(f'Obligation: {oblig.title}')

            # Create obligation spec
            spec, _ = ObligationSpec.objects.get_or_create(
                obligation=oblig,
                schema=['http://example.com'],
                workflow_class=WORKFLOW,
                is_current=True
            )

            print(f'Obligation specification: {str(spec)}')

            rep_cycle, _ = ReportingCycle.objects.get_or_create(
                obligation=oblig,
                obligation_spec=spec,
                reporting_start_date=timezone.now().replace(
                    month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
                is_open=True,
            )

            print(f'Reporting cycle: {str(rep_cycle)}')

            for rep_abbr in [r for r in REPORTERS if r in OBLIGATIONS_REPORTERS_MAP[oblig_code]]:
                try:
                    rep = Reporter.objects.get(abbr=rep_abbr)
                except Reporter.DoesNotExist:
                    print(f'ERROR: could not find reporter "{rep_abbr}"')
                    continue

                print(f'\tReporter: {str(rep)}')

                # Map reporters to obligation spec
                spec_rep, _ = ObligationSpecReporter.objects.get_or_create(spec=spec, reporter=rep)

                # Create per-reporter group for obligation
                oblig_group, _ = Group.objects.get_or_create(
                    name=f'{oblig_group_prefix}-{rep_abbr.lower()}'
                )

                print(f'\tCreating group: "{oblig_group.name}"')
                # Assign model permissions
                for perm in reporting_model_perms:
                    oblig_group.permissions.add(perm)

                # Assign object permissions on Reporter and Obligation
                assign_perm(reporter_perm, oblig_group, rep)
                assign_perm(oblig_perm, oblig_group, oblig)
