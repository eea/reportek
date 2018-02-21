from django.contrib.auth.models import (
    AbstractUser,
    Group,
)

from django_auth_ldap.backend import LDAPBackend
from guardian.mixins import GuardianUserMixin
from guardian.shortcuts import (
    get_objects_for_user,
    get_objects_for_group,
)


__all__ = [
    'ReportekUser',
]


class ReportekUser(GuardianUserMixin, AbstractUser):

    @property
    def ldap_groups(self):
        """
        Returns QuerySet with `Group`s in which the user is a virtual member
        through LDAP.
        """
        if not hasattr(self, 'ldap_user'):
            user = LDAPBackend().populate_user(self.username)
            if user is None:
                return []
        else:
            user = self
        return Group.objects.filter(name__in=user.ldap_user.group_names)

    @property
    def effective_groups(self):
        """
        Returns `QuerySet` of `Group`s in which the user is a member either
        directly or through LDAP.
        """
        return self.groups.union(self.ldap_groups)

    def get_effective_objects(self, perms, klass=None):
        """
        Gets objects of type `klass` for which the user has _all_ permissions
        in `perms`, either directly or through groups (both direct membership
        and LDAP).

        Args:
            perms: String or list of strings with permission names. Note that
                names must include the app prefix if `klass` is not provided.
            klass: may be a Model, Manager or QuerySet object. If not given this
            parameter would be computed based on given `perms`.

        Returns:
            QuerySet: The objects covered by permissions.
        """
        user_objs = get_objects_for_user(self, perms, klass)
        ldap_obj_qs = [get_objects_for_group(grp, perms, klass) for grp in self.ldap_groups]
        return user_objs.union(*ldap_obj_qs)

    def get_reporters(self):
        """Returns `Reporter`s for which the user has permission to report."""
        return self.get_effective_objects('core.report_for_reporter').all()

    def get_obligations(self):
        """Returns `Obligation`s on which the user has permission to report."""
        return self.get_effective_objects('core.report_on_obligation').all()