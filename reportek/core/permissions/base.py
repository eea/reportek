import logging
from rest_framework.permissions import (
    BasePermission,
    IsAuthenticated,
    DjangoObjectPermissions,
    SAFE_METHODS,
    Http404,
)

from reportek.core.utils import basic_auth_login

from .utils import get_effective_obj_perms


log = logging.getLogger('reportek.perms')
info = log.info
debug = log.debug
warn = log.warning
error = log.error


class IsAnonymous(BasePermission):
    def has_permission(self, request, view):
        return not request.user.is_authenticated()


class BasePermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        # don't return True by default
        return self.has_permission(request, view)


class IsAuthenticated(BasePermission, IsAuthenticated):
    def has_permission(self, request, view):
        request = basic_auth_login(request)
        return super().has_permission(request, view) and request.user.is_active


class IsAuthenticatedOrEnvelopeIsPublic(IsAuthenticated):
    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return obj.finalized or super().has_permission(request, view)


class EffectiveObjectPermissions(DjangoObjectPermissions):

    def get_required_permissions(self, method, model_cls):
        perms = super().get_required_permissions(method, model_cls)
        debug(f'{model_cls.__name__} req. perms: {perms}')
        return perms

    def get_required_object_permissions(self, method, model_cls):
        perms = super().get_required_object_permissions(method, model_cls)
        debug(f'{model_cls.__name__} req. obj. perms: {perms}')
        return perms

    def has_object_permission(self, request, view, obj):
        # authentication checks have already executed via has_permission
        queryset = self._queryset(view)
        model_cls = queryset.model
        # user = request.user
        eff_groups = request.user.effective_groups

        perms = self.get_required_object_permissions(request.method, model_cls)

        eff_perms = get_effective_obj_perms(eff_groups, obj)

        print(perms, eff_perms)
        # if not user.has_perms(perms, obj):
        if not set(perms).issubset(eff_perms):
            # If the user does not have permissions we need to determine if
            # they have read permissions to see 403, or not, and simply see
            # a 404 response.

            if request.method in SAFE_METHODS:
                # Read permissions already checked and failed, no need
                # to make another lookup.
                raise Http404

            read_perms = self.get_required_object_permissions('GET', model_cls)
            # if not user.has_perms(read_perms, obj):
            if not set(read_perms).issubset(eff_perms):
                raise Http404

            # Has read permissions.
            return False

        return True
