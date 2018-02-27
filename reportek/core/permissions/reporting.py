import logging
from django.db.models import ObjectDoesNotExist
from rest_framework.permissions import (
    DjangoObjectPermissions,
    SAFE_METHODS,
)

from ..models import (
    ObligationSpec,
    Reporter,
    Envelope,
)

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


class EnvelopePermissions(DjangoObjectPermissions):

    def get_required_permissions(self, method, model_cls):
        perms = super().get_required_permissions(method, model_cls)
        debug(f'Envelope req. perms: {perms}')
        return perms

    def has_permission(self, request, view):
        perms = super().has_permission(request, view)
        debug(f'Envelope perms: {perms}')
        if not perms:
            return False
        if request.method in SAFE_METHODS:
            return True
        elif request.method == 'POST':
            reporter_id = request.data.get('reporter')
            obligation_spec_id = request.data.get('obligation_spec')
            try:
                reporter = Reporter.objects.get(pk=reporter_id)
                obligation_spec = ObligationSpec.objects.get(pk=obligation_spec_id)
            except ObjectDoesNotExist:
                return False

            # Creating an envelope requires permission to report on
            # the obligation on behalf of the reporter.
            groups = request.user.effective_groups
            return (
                'report_for_reporter' in get_effective_obj_perms(groups, reporter) and
                'report_on_obligation' in get_effective_obj_perms(groups, obligation_spec.obligation)
            )

    def get_required_object_permissions(self, method, model_cls):
        perms = super().get_required_object_permissions(method, model_cls)
        debug(f'Envelope req. obj. perms: {perms}')
        return perms

    def has_object_permission(self, request, view, envelope):
        perms = super().has_object_permission(request, view, envelope)
        debug(f'Envelope obj. perms: {perms}')
        if not perms:
            return False
        if request.method in SAFE_METHODS:
            return request.user == envelope.author or \
                   envelope.finalized or \
                   request.user.has_perm('core.act_as_reportnet_api')
        elif request.method == 'PATCH':
            return request.user == envelope.author and not envelope.finalized
        elif request.method == 'DELETE':
            return request.user == envelope.author and not envelope.finalized


class EnvelopeFilePermissions(DjangoObjectPermissions):

    def get_required_permissions(self, method, model_cls):
        perms = super().get_required_permissions(method, model_cls)
        debug(f'EnvelopeFile req. perms: {perms}')
        return perms

    def has_permission(self, request, view):
        perms = super().has_permission(request, view)
        debug(f'EnvelopeFile perms: {perms}')
        if not perms:
            return False
        if request.method in SAFE_METHODS:
            return True
        elif request.method == 'POST':
            envelope_id = request.data.get('envelope_pk')
            try:
                envelope = Envelope.objects.get(pk=envelope_id)
            except ObjectDoesNotExist:
                return False

            # Creating an envelope file requires an envelope in a state
            # that allows uploads, and permission to report/collaborate
            # on the obligation on behalf of the reporter.
            if not envelope.workflow.upload_allowed:
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

    def get_required_object_permissions(self, method, model_cls):
        perms = super().get_required_object_permissions(method, model_cls)
        debug(f'EnvelopeFile req. obj. perms: {perms}')
        return perms

    def has_object_permission(self, request, view, envelope_file):
        perms = super().has_object_permission(request, view, envelope_file)
        debug(f'EnvelopeFile obj. perms: {perms}')
        if not perms:
            return False
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
