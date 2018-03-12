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

from .utils import (
    get_effective_obj_perms,
    debug_call,
)


log = logging.getLogger('reportek.auth')
info = log.info
debug = log.debug
warn = log.warning
error = log.error


__all__ = [
    'EnvelopePermissions',
    'EnvelopeFilePermissions',
    'EnvelopeOriginalFilePermissions',
]


def has_reporter_permissions(groups, reporter, obligation):
    return (
        'report_for_reporter' in get_effective_obj_perms(groups, reporter) and
        'report_on_obligation' in get_effective_obj_perms(groups, obligation)
    )


def has_collaborator_permissions(groups, reporter, obligation):
    return (
        'collaborate_for_reporter' in get_effective_obj_perms(groups, reporter) and
        'report_on_obligation' in get_effective_obj_perms(groups, obligation)
    )


class EnvelopePermissions(EffectiveObjectPermissions):

    @debug_call
    def has_permission(self, request, view):
        perms = super().has_permission(request, view)
        if not perms:
            return False
        if request.method in SAFE_METHODS:
            return True
        elif request.method == 'POST':
            # Creating or other POSTS on an envelope requires permission to report on
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
                return has_reporter_permissions(groups, reporter, obligation_spec.obligation)
            else:
                # Non-create POST requests, e.g. `transition`
                try:
                    envelope = Envelope.objects.get(pk=request.resolver_match.kwargs.get('pk'))
                except Envelope.DoesNotExist:
                    return False

                return has_reporter_permissions(groups, envelope.reporter, envelope.obligation_spec.obligation)

        # Allow GET detail, PATCH, PUT & DELETE to fall through to `has_object_permissions`
        return True

    @debug_call
    def has_object_permission(self, request, view, envelope):
        # We do NOT check object permissions on the Envelope object itself,
        # as there are none currently in use.
        if request.method in SAFE_METHODS:
            return True
        elif request.method == 'PATCH':
            return request.user == envelope.author and not envelope.finalized
        elif request.method == 'DELETE':
            return request.user == envelope.author and not envelope.finalized
        elif request.method == 'POST' and view.action != 'create':
            return request.user == envelope.author and not envelope.finalized

        return False


class BaseEnvelopeFilePermissions(EffectiveObjectPermissions):

    @debug_call
    def has_permission(self, request, view):
        perms = super().has_permission(request, view)
        if not perms:
            return False
        if request.method in SAFE_METHODS:
            return True
        elif request.method == 'POST' and view.action == 'create':
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
            has_reporter_permissions(groups, envelope.reporter, envelope.obligation_spec.obligation) or
            has_collaborator_permissions(groups, envelope.reporter, envelope.obligation_spec.obligation)
        )

    @debug_call
    def has_object_permission(self, request, view, envelope_file):
        # We do NOT check object permissions on the EnvelopeFile object itself,
        # as there are none currently in use.
        envelope = envelope_file.envelope
        if request.method in SAFE_METHODS:
            return True
        elif request.method == 'PATCH':
            return request.user == envelope.author and not envelope.finalized
        elif request.method == 'DELETE':
            return request.user == envelope.author and not envelope.finalized
        elif request.method == 'POST' and view.action != 'create':
            return request.user == envelope.author and not envelope.finalized

        return False


class EnvelopeFilePermissions(BaseEnvelopeFilePermissions):
    pass


class EnvelopeOriginalFilePermissions(BaseEnvelopeFilePermissions):
    pass
