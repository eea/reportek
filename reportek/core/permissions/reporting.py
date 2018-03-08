import logging
from django.db.models import ObjectDoesNotExist
from rest_framework.permissions import (
    SAFE_METHODS,
)

from ..models import (
    ObligationSpec,
    Reporter,
    Envelope,
)

from .base import EffectiveObjectPermissions
from .utils import get_effective_obj_perms


log = logging.getLogger('reportek.perms')
info = log.info
debug = log.debug
warn = log.warning
error = log.error


__all__ = [
    'EnvelopePermissions',
    'EnvelopeFilePermissions',
]


class EnvelopePermissions(EffectiveObjectPermissions):

    def has_permission(self, request, view):
        perms = super().has_permission(request, view)
        debug(f'Envelope perms: {perms}')
        if not perms:
            return False
        if request.method in SAFE_METHODS:
            return True
        elif request.method == 'POST':
            # Creating or transitioning an envelope requires permission to report on
            # the obligation on behalf of the reporter.
            groups = request.user.effective_groups
            if view.action == 'create':
                reporter_id = request.data.get('reporter')
                obligation_spec_id = request.data.get('obligation_spec')
                try:
                    reporter = Reporter.objects.get(pk=reporter_id)
                    obligation_spec = ObligationSpec.objects.get(pk=obligation_spec_id)
                except ObjectDoesNotExist:
                    return False
                return (
                    'report_for_reporter' in get_effective_obj_perms(groups, reporter) and
                    'report_on_obligation' in get_effective_obj_perms(groups, obligation_spec.obligation)
                )
            elif view.action == 'transition':
                try:
                    envelope = Envelope.objects.get(pk=request.resolver_match.kwargs.get('pk'))
                except Envelope.DoesNotExist:
                    return False

                return (
                    'report_for_reporter' in get_effective_obj_perms(groups, envelope.reporter) and
                    'report_on_obligation' in get_effective_obj_perms(groups, envelope.obligation_spec.obligation)
                )

        # Allow GET detail, PATCH, PUT & DELETE to fall through to `has_object_permissions`
        return True

    def has_object_permission(self, request, view, envelope):
        if request.method in SAFE_METHODS:
            return request.user == envelope.author or \
                   envelope.finalized or \
                   request.user.has_perm('core.act_as_reportnet_api')
        elif request.method == 'PATCH':
            return request.user == envelope.author and not envelope.finalized
        elif request.method == 'DELETE':
            return request.user == envelope.author and not envelope.finalized
        elif request.method == 'POST' and view.action != 'create':
            return request.user == envelope.author and not envelope.finalized

        return False


class EnvelopeFilePermissions(EffectiveObjectPermissions):

    def has_permission(self, request, view):
        perms = super().has_permission(request, view)
        debug(f'EnvelopeFile perms: {perms}')
        if not perms:
            return False
        if request.method in SAFE_METHODS:
            return True
        elif request.method == 'POST':
            if view.action == 'create':
                envelope_id = request.data.get('envelope_pk')
            else:
                envelope_id = request.resolver_match.kwargs.get('envelope_pk')

            try:
                envelope = Envelope.objects.get(pk=envelope_id)
            except ObjectDoesNotExist:
                return False

            # Creating an envelope file requires an envelope in a state
            # that allows uploads, and permission to report/collaborate
            # on the obligation on behalf of the reporter.
            if view.action == 'create' and not envelope.workflow.upload_allowed:
                return False

            groups = request.user.effective_groups
            return (
                (
                    'report_for_reporter' in get_effective_obj_perms(groups, envelope.reporter) and
                    'report_on_obligation' in get_effective_obj_perms(groups, envelope.obligation_spec.obligation)
                ) or
                (
                    'collaborate_for_reporter' in get_effective_obj_perms(groups, envelope.reporter) and
                    'report_on_obligation' in get_effective_obj_perms(groups, envelope.obligation_spec.obligation)
                )
            )

        # Allow GET detail, PATCH, PUT & DELETE to fall through to `has_object_permissions`
        return True

    def has_object_permission(self, request, view, envelope_file):
        envelope = envelope_file.envelope
        if request.method in SAFE_METHODS:
            groups = request.user.effective_groups
            # Allow read for:
            # - author
            # - public if finalized and not restricted
            # - obligation's client
            # - Reportnet APIs
            debug(f'[EnvelopeFile obj perms] Groups: {groups}')
            return request.user == envelope.author or \
                request.user.has_perm('core.act_as_reportnet_api') or \
                (envelope.finalized and not envelope_file.restricted) or \
                (envelope.finalized and
                 'inspect_deliveries' in
                 get_effective_obj_perms(groups, envelope_file.envelope.obligation_spec.obligation.client))
        elif request.method == 'PATCH':
            return request.user == envelope.author and not envelope.finalized
        elif request.method == 'DELETE':
            return request.user == envelope.author and not envelope.finalized
        elif request.method == 'POST' and view.action != 'create':
            return request.user == envelope.author and not envelope.finalized

        return False
