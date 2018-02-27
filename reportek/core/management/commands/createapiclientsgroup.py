from django.core.management.base import BaseCommand
from django.conf import settings

from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):

    help = f'Create the group for Reportnet API clients ({settings.REPORTNET_API_CLIENTS_GROUP})'

    def handle(self, **options):
        api_clients_group, _ = Group.objects.get_or_create(name=settings.REPORTNET_API_CLIENTS_GROUP)
        user_type = ContentType.objects.get(app_label='core', model='reportekuser')
        api_client_perm = Permission.objects.get(content_type=user_type, codename='act_as_reportnet_api')
        if api_client_perm not in api_clients_group.permissions.all():
            api_clients_group.permissions.add(api_client_perm)
