from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):

    help = "Load ROD initial data"

    FIXTURES = ('countries', 'instruments', 'issues', 'clients', 'obligations')

    def handle(self, *args, **options):
        for fixture in Command.FIXTURES:
            call_command('loaddata', fixture)
