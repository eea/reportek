import logging
from functools import wraps
import itertools
from django.contrib.auth.models import Permission
from guardian.shortcuts import get_perms


log = logging.getLogger('reportek.auth')
info = log.info
debug = log.debug
warn = log.warning
error = log.error


def get_groups_obj_perms(groups, obj):
    """
    Builds the set of object permissions found in a list of groups
    for a model instance.
    Intended for use in combination with `get_effective_groups` to get
    a user's effective object privileges, e.g.:
    ```
    user_groups = groups = get_effective_groups(request.user)
    get_groups_obj_perms(groups, envelope.reporter)
    ```

    Params:
        groups: List of `Group` instances
        obj: A model instance.

    Returns:
         A set of permissions names.
    """
    eff_perms = set(
        itertools.chain.from_iterable([get_perms(grp, obj) for grp in groups])
    )
    debug(
        f'Effective permissions of groups {[g.name for g in groups]} '
        f'on {obj.__class__.__name__} "{obj}": {eff_perms}'
    )
    return eff_perms


def get_groups_perms(groups):
    """
    Builds the set of (model) permissions found in a list of groups.
    Intended for use in combination with `get_effective_groups` to get
    a user's effective privileges, e.g.:
    ```
    user_groups = groups = get_effective_groups(request.user)
    get_groups_perms(groups)
    ```

    Params:
        groups: List of `Group` instances

    Returns:
         A set of permissions names, namespaced with the app label.
    """
    eff_perms = Permission.objects.filter(group__in=groups).order_by(
        'codename'
    ).distinct(
        'codename'
    )
    eff_perms = set([f'{p.content_type.app_label}.{p.codename}' for p in eff_perms])
    debug(f'Effective permissions of groups {[g.name for g in groups]}: {eff_perms}')
    return eff_perms


def debug_call(f):
    """
    Wrapper for `has_permissions` | `has_object_permissions`,
    logs the call and result.
    """

    @wraps(f)
    def wrapper(self, request, view, *args, **kwargs):
        r = f(self, request, view, *args, **kwargs)
        debug(
            f'{request.method} [{view.action}] in {self.__class__.__name__}.{f.__name__}() -> {r}'
        )
        return r

    return wrapper


def skip_for_superuser(f):
    """
    Wrapper for `has_permissions` | `has_object_permissions`, skips checks for superusers.ß
    """

    @wraps(f)
    def wrapper(self, request, view, *args, **kwargs):
        return request.user.is_superuser or f(self, request, view, *args, **kwargs)

    return wrapper
