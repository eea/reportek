import itertools
from django.contrib.auth.models import (
    AbstractUser,
    Group,
)

from django_auth_ldap.backend import LDAPBackend
from guardian.mixins import GuardianUserMixin

__all__ = [
    'ReportekUser',
]


class ReportekUser(GuardianUserMixin, AbstractUser):

    @property
    def ldap_groups(self):
        if not hasattr(self, 'ldap_user'):
            user = LDAPBackend().populate_user(self.username)
            if user is None:
                return []
        else:
            user = self
        ldap_groups = Group.objects.filter(name__in=user.ldap_user.group_names).all()
        return ldap_groups

    @property
    def ldap_group_names(self):
        return [grp.name for grp in self.ldap_groups]

    @property
    def effective_groups(self):
        django_groups = self.groups.all()
        eff_groups = set(
            list(
                itertools.chain(self.ldap_groups, django_groups)
            )
        )
        return eff_groups

    @property
    def effective_group_names(self):
        return [grp.name for grp in self.effective_groups]
