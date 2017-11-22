from django.core.management.base import BaseCommand, CommandError

from reportek.core.models import ObligationGroup


class Command(BaseCommand):
    help = "Start a new reporting cycle for each due obligation."

    def handle(self, *args, **options):
        ogs = ObligationGroup.objects.pending()
        for og in ogs:
            og.start_reporting_period()

        if len(ogs) == 0:
            self.stdout.write("No obligation groups pending.")
        else:
            self.stdout.write(self.style.SUCCESS(
                "Started reporting cycle for %d obligation groups:" % len(ogs)
            ))
            self.stdout.write("\n".join("- %s" % og.name for og in ogs))
