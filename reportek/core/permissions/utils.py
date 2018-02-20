import logging
import itertools
from django.contrib.auth.models import Group
from guardian.shortcuts import get_perms


log = logging.getLogger('reportek.perms')
info = log.info
debug = log.debug
warn = log.warning
error = log.error


def get_effective_groups(user):
    """
    Returns a set of `Group` instances corresponding to
    the user's LDAP group and Django group memberships.

    Params:
        user: A `User` instance.
    """
    ldap_groups = Group.objects.filter(name__in=user.ldap_user.group_names).all()
    django_groups = user.groups.all()
    eff_groups = set(
        list(
            itertools.chain(ldap_groups, django_groups)
        )
    )
    debug(f'Effective groups of user "{user}": {[g.name for g in eff_groups]}')
    return eff_groups


def get_effective_obj_perms(groups, obj):
    """
    Builds the set of object permissions found in a list of groups
    for a model instance.
    Intended for use in combination with `get_effective_groups` to get
    a user's effective object privileges, e.g.:
    ```
    user_groups = groups = get_effective_groups(request.user)
    get_effective_obj_perms(groups, envelope.reporter)
    ```

    Params:
        groups: List of `Group` instances
        obj: A model instance.

    Returns:
         A set of permissions names.
    """
    eff_perms = set(
        itertools.chain.from_iterable(
            [get_perms(grp, obj) for grp in groups]
        )
    )
    debug(f'Effective permissions of groups {[g.name for g in groups]} '
          f'on {obj.__class__.__name__} "{obj}": {eff_perms}')
    return eff_perms
