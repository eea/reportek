import os
from pathlib import Path
import logging
from base64 import b64encode
from rest_framework import viewsets, status
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.authentication import (
    TokenAuthentication
)

from django.conf import settings
from django.core.files import File
from django.utils import timezone

from ..models import (
    Envelope,
    EnvelopeFile,
    BaseWorkflow,
    Obligation,
    Country,
    UploadToken,
)
from ..serializers import (
    EnvelopeSerializer,
    EnvelopeFileSerializer, CreateEnvelopeFileSerializer,
    NestedEnvelopeWorkflowSerializer
)
from .. import permissions

log = logging.getLogger('reportek.workflows')
info = log.info
debug = log.debug
warn = log.warning
error = log.error


class EnvelopeResultsSetPagination(LimitOffsetPagination):
    default_limit = 20
    max_limit = 100


class EnvelopeViewSet(viewsets.ModelViewSet):
    queryset = Envelope.objects.all().prefetch_related('files')
    serializer_class = EnvelopeSerializer
    authentication_classes = viewsets.ModelViewSet.authentication_classes + [TokenAuthentication]
    permission_classes = (permissions.IsAuthenticated, )
    pagination_class = EnvelopeResultsSetPagination

    @detail_route(methods=['post'])
    def transition(self, request, pk):
        """
        Initiates a transition, expects `transition_name` in the POST data.
        """

        envelope = self.get_object()
        workflow = envelope.workflow
        transition_name = request.data.get('transition_name')

        def make_response(with_error=None):
            response = {
                'transition': transition_name,
                'current_state': workflow.current_state,
            }
            if with_error:
                response['error'] = with_error
            return response

        try:
            workflow.start_transition(transition_name)
        except BaseWorkflow.TransitionDoesNotExist as err:
            return Response(
                make_response(with_error=str(err)),
                status=status.HTTP_400_BAD_REQUEST
            )
        except BaseWorkflow.TransitionNotAvailable as err:
            return Response(
                make_response(with_error=str(err)),
                status=status.HTTP_406_NOT_ACCEPTABLE
            )
        except Exception as err:
            return Response(
                make_response(with_error=str(err)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(make_response())

    @detail_route(methods=['get'])
    def history(self, request, pk):
        """
        Returns an evelope's transition history.
        """
        envelope = self.get_object()
        workflow = envelope.workflow
        return Response(
            {
                ev.timestamp.isoformat(): {
                    'transition': ev.transition,
                    'from_state': ev.from_state,
                    'to_state': ev.to_state
                }
                for ev in workflow.history.all()
            }
        )

    @list_route(methods=['get'])
    def status(self, request):
        """
        Returns a paginated list of envelopes matching the provided params:
            - `country`: an ISO country code (multiple occurences allowed)
            - `obligation`: an obligation id (multiple occurences allowed)
            - `finalized`: 0/1 flag indicating envelope finalization status
        """
        countries = request.query_params.getlist('country')
        obligations = request.query_params.getlist('obligation')
        finalized = request.query_params.get('finalized')

        envelopes = Envelope.objects.prefetch_related('files')

        if countries:
            countries = Country.objects.filter(iso__in=countries).all()
            envelopes = envelopes.filter(country__in=countries)

        if obligations:
            obligation_ids = []
            for o in obligations:
                try:
                    obligation_ids.append(int(o))
                except ValueError:
                    pass

            obligations = Obligation.objects.filter(pk__in=obligation_ids).all()
            obligation_groups = set([o.group for o in obligations])
            envelopes = envelopes.filter(obligation_group__in=obligation_groups)

        if finalized is not None:
            try:
                finalized = bool(int(finalized))
                envelopes = envelopes.filter(finalized=finalized)
            except ValueError:
                pass

        envelopes = envelopes.order_by(
            'country',
            'obligation_group',
            '-updated_at'
        )

        page = self.paginate_queryset(envelopes)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(envelopes, many=True)
        return Response(serializer.data)

    @detail_route(methods=['post'])
    def token(self, request, pk):
        """
        Creates an `UploadToken` for the envelope.
        Used by `tusd` uploads server for user/envelope correlation.
        Upload tokens cannot be issued for finalized envelopes.

        Returns:
         ```
         {
            'token': <base64 encoded token>
         }
         ```
        """
        envelope = self.get_object()
        if envelope.finalized:
            return Response(
                {'error': 'envelope is finalized'},
                status=status.HTTP_400_BAD_REQUEST
            )
        token = envelope.upload_tokens.create(user=request.user)
        return Response(
            {
                'token': b64encode(token.token.encode())
            }
        )


class EnvelopeFileViewSet(viewsets.ModelViewSet):
    queryset = EnvelopeFile.objects.all()
    permission_classes = (permissions.IsAuthenticated, )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateEnvelopeFileSerializer
        return EnvelopeFileSerializer

    def get_queryset(self):
        return super().get_queryset().filter(
            envelope_id=self.kwargs['envelope_pk']
        )

    def perform_create(self, serializer):
        serializer.save(
            envelope_id=self.kwargs['envelope_pk']
        )


class EnvelopeWorkflowViewSet(viewsets.ModelViewSet):
    queryset = BaseWorkflow.objects.all()
    serializer_class = NestedEnvelopeWorkflowSerializer
    permission_classes = (permissions.IsAuthenticated, )


class UploadHookView(viewsets.ViewSet):
    """
    Handles upload notifications from tusd.
    """
    TUS_HOOKS = [
        'pre-create',
        'post-create',
        'post-finish',
        'post-terminate',
        'post-receive'
    ]

    @staticmethod
    def handle_pre_create(request):
        """
        Handles a pre-create notification from `tusd`.

        Returns an OK response only if:
         - the upload `token` the `MetaData` field is validated
         - the token's user is authenticated
         - a `filename` field is present in `MetaData`
        """

        info(f'UPLOAD pre-create: {request.data}')
        meta_data = request.data.get('MetaData', {})
        tok = meta_data.get('token', '')
        try:
            token = UploadToken.objects.get(token=tok)

            # Token validity check allows a grace period
            if token.valid_until < timezone.now() + timezone.timedelta(seconds=30):
                token.delete()
                error('UPLOAD denied: EXPIRED TOKEN')
                return Response(
                    {'error': 'expired token'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # TODO Validate user access to envelope when roles are in place
            if not token.user.is_authenticated():
                error(f'UPLOAD denied on envelope "{token.envelope}" '
                      f'for "{token.user}": NOT ALLOWED')
                return Response(
                    {'error': 'user not authenticated'},
                    status=status.HTTP_403_FORBIDDEN
                )

            if meta_data.get('filename') is None:
                error(f'UPLOAD denied on envelope "{token.envelope}" '
                      f'for "{token.user}": filename is missing')
                return Response(
                    {'error': 'filename not in MetaData'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            info(f'UPLOAD authorized on envelope "{token.envelope}" for "{token.user}"')

        except UploadToken.DoesNotExist:
            error('UPLOAD denied: INVALID TOKEN')
            return Response(
                {'error': 'invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response()

    @staticmethod
    def handle_post_receive(request):
        """
        Handles a post-receive notification from `tusd`.
        Currently has no side-effects, exists only to avoid
        'hook not implemented' errors in `tusd`.
        """
        info(f'UPLOAD post-receive: {request.data}')
        return Response()

    @staticmethod
    def handle_post_create(request):
        """
        Handles a post-create notification from `tusd`.
        Currently has no side-effects, exists only to avoid
        'hook not implemented' errors in `tusd`.
        """
        info(f'UPLOAD post-create: {request.data}')
        return Response()

    @staticmethod
    def handle_post_finish(request):
        """
        Handles a post-finish notification from `tusd`.
        The uploaded file is used to create an EnvelopeFile.
        """
        info(f'UPLOAD post-finish: {request.data}')
        meta_data = request.data.get('MetaData', {})
        tok = meta_data.get('token', '')
        # filename presence was enforced during pre-create
        file_name = meta_data['filename']
        try:
            token = UploadToken.objects.get(token=tok)
            # TODO Validate user access to envelope when roles are in place
            if not token.user.is_authenticated():
                error(f'UPLOAD denied on envelope "{token.envelope}" '
                      f'for "{token.user}": NOT ALLOWED')
                return Response(
                    {'error': 'user not authenticated'},
                    status=status.HTTP_403_FORBIDDEN
                )
            file_path = os.path.join(
                settings.TUSD_UPLOADS_DIR,
                f'{request.data.get("ID")}.bin'
            )

            file_path = Path(file_path).resolve()
            if not file_path.is_file():
                raise FileNotFoundError

            # Overrite envelope file if it exists
            try:
                envelope_file = EnvelopeFile.objects.get(
                    envelope=token.envelope,
                    name=file_name
                )
                # Delete existing file to avoid renaming in `Storage.get_available_name`
                old_file = os.path.join(
                    settings.PROTECTED_ROOT,
                    envelope_file.get_envelope_directory(file_name)
                )
                info(f'UPLOAD deleting old file: {old_file}')
                try:
                    os.remove(old_file)
                except FileNotFoundError:
                    warn('UPLOAD could not find old upload "{old_file}"')
            except EnvelopeFile.DoesNotExist:
                envelope_file = EnvelopeFile(
                    envelope=token.envelope,
                    name=file_name
                )
            # Save the file through the protected storage field
            envelope_file.file.save(file_name, File(file_path.open()))

            # Finally, remove the token
            token.delete()

        except UploadToken.DoesNotExist:
            error(f'UPLOAD denied on envelope "{token.envelope}" '
                  f'for "{token.user}": INVALID TOKEN')
            return Response(
                {'error': 'invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except FileNotFoundError:
            error(f'UPLOAD file does not exist: "{file_path}"')
            return Response(
                {'error': 'file not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response()

    @staticmethod
    def handle_post_terminate(request):
        """
        Handles a post-terminate notification from `tusd`.
        Currently has no side-effects, exists only to avoid
        'hook not implemented' errors in `tusd`.
        """
        info(f'UPLOAD post-terminate: {request.data}')
        return Response()

    def create(self, request):
        """
        Dispatches notifications from `tusd` to appropriate handler.
        """
        # Original header name sent by tusd is `Hook-Name`, Django mangles it
        hook_name = self.request.META.get('HTTP_HOOK_NAME')
        try:
            return getattr(self, f'handle_{hook_name.replace("-", "_")}')(request)
        except AttributeError:
            return Response(
                {'hook_not_supported': hook_name},
                status=status.HTTP_400_BAD_REQUEST
            )
