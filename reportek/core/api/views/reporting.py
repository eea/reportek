import os
from pathlib import Path
from zipfile import ZipFile, BadZipFile
from collections import OrderedDict
import logging
from base64 import b64encode
from django.views import static
from django.db.models import Q, F, Exists, OuterRef
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework.renderers import StaticHTMLRenderer, TemplateHTMLRenderer
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.authentication import (
    TokenAuthentication
)

from django.conf import settings
from django.core.files import File

from ...models import (
    Envelope,
    EnvelopeFile,
    BaseWorkflow,
    Obligation,
    Reporter,
    UploadToken,
    QAJob,
)

from ...serializers import (
    EnvelopeSerializer,
    EnvelopeFileSerializer, CreateEnvelopeFileSerializer,
    NestedEnvelopeWorkflowSerializer,
    NestedUploadTokenSerializer,
    QAJobSerializer,
)

from ... import permissions

from reportek.core.utils import path_parts

from reportek.core.qa import RemoteQA
from reportek.core.conversion import RemoteConversion
from reportek.core.utils import fully_qualify_url


log = logging.getLogger('reportek')
info = log.info
debug = log.debug
warn = log.warning
error = log.error

__all__ = [
    'EnvelopeViewSet',
    'EnvelopeFileViewSet',
    'EnvelopeWorkflowViewSet',
    'UploadTokenViewSet',
    'UploadHookView',
]


class EnvelopeResultsSetPagination(LimitOffsetPagination):
    default_limit = 20
    max_limit = 100


class EnvelopeViewSet(viewsets.ModelViewSet):
    queryset = Envelope.objects.all().prefetch_related('files')
    serializer_class = EnvelopeSerializer
    authentication_classes = viewsets.ModelViewSet.authentication_classes + [TokenAuthentication]
    permission_classes = (
        permissions.EnvelopePermissions,
    )
    pagination_class = EnvelopeResultsSetPagination

    def perform_create(self, serializer):
        serializer.validated_data['author'] = self.request.user
        return super().perform_create(serializer)

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
        reporters = request.query_params.getlist('reporter')
        obligations = request.query_params.getlist('obligation')
        finalized = request.query_params.get('finalized')

        envelopes = Envelope.objects.prefetch_related('files')

        if reporters:
            reporters = Reporter.objects.filter(abbr__in=reporters).all()
            envelopes = envelopes.filter(reporter__in=reporters)

        if obligations:
            obligation_ids = []
            for o in obligations:
                try:
                    obligation_ids.append(int(o))
                except ValueError:
                    pass

            obligations = Obligation.objects.filter(pk__in=obligation_ids).all()
            envelopes = envelopes.filter(obligation__in=obligations)

        if finalized is not None:
            try:
                finalized = bool(int(finalized))
                envelopes = envelopes.filter(finalized=finalized)
            except ValueError:
                pass

        envelopes = envelopes.order_by(
            'reporter',
            '-updated_at'
        )

        page = self.paginate_queryset(envelopes)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(envelopes, many=True)
        return Response(serializer.data)

    @detail_route(methods=['get'])
    def feedback(self, request, pk):
        """
        Returns a paginated list of completed QA jobs for the envelope's files.
        """
        envelope = self.get_object()
        qa_jobs = QAJob.objects.filter(completed=True, envelope_file__envelope=envelope)

        page = self.paginate_queryset(qa_jobs)
        if page is not None:
            serializer = QAJobSerializer(page, many=True, context={'request': request})
            pager = self.paginator
            # Inject QA completion information in pager metadata
            response = Response(OrderedDict([
                ('auto_qa_completed', envelope.auto_qa_complete),
                ('auto_qa_ok', envelope.auto_qa_ok),
                ('count', pager.count),
                ('next', pager.get_next_link()),
                ('previous', pager.get_previous_link()),
                ('results', serializer.data)
            ]))
            return response

        serializer = QAJobSerializer(qa_jobs, many=True, context={'request': request})
        return Response(
            {
                'qa_completed': envelope.auto_qa_complete,
                'results': serializer.data
            }
        )

    @detail_route(methods=['get'])
    def workflow_graph(self, request, pk):
        """
        Returns an evelope's workflow represented as a JSON graph.
        """
        envelope = self.get_object()
        return Response(envelope.workflow.to_json_graph())


class EnvelopeFileViewSet(viewsets.ModelViewSet):
    queryset = EnvelopeFile.objects.all()
    permission_classes = (
        permissions.EnvelopeFilePermissions,
    )

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateEnvelopeFileSerializer
        return EnvelopeFileSerializer

    def get_queryset(self):
        return super().get_queryset().filter(
            envelope_id=self.kwargs['envelope_pk']
        )

    def perform_create(self, serializer):
        serializer.save(
            envelope_id=self.kwargs['envelope_pk'],
            uploader_id=self.request.user.pk,
        )

    def destroy(self, request, envelope_pk, pk=None):
        """
        Serves `DELETE` requests on both list and detail routes.
        List deletes must provide the ids of the envelope files to delete
        as a URL string, using the format: `ids=<ID1>,...,<IDn>`.
        """
        if pk is not None:
            return super().destroy(envelope_pk, pk)
        else:
            ids = request.query_params.get('ids', '')
            try:
                ids = [int(i) for i in ids.split(',')]
            except ValueError:
                return Response(status=status.HTTP_404_NOT_FOUND)
            if not ids or len(ids) != EnvelopeFile.objects.filter(envelope_id=envelope_pk, id__in=ids).count():
                return Response(status=status.HTTP_404_NOT_FOUND)
            EnvelopeFile.objects.filter(id__in=ids).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['get', 'head'], renderer_classes=(StaticHTMLRenderer,))
    def download(self, request, envelope_pk, pk):
        envelope_file = self.get_object()
        _file = envelope_file.file
        relpath = _file.name

        if relpath is None or relpath == '':
            return Response(status=status.HTTP_404_NOT_FOUND)

        if settings.DEBUG:
            response = static.serve(
                request,
                path=relpath,
                document_root=_file.storage.location)
        else:
            # this does "X-Sendfile" on nginx, see
            # https://www.nginx.com/resources/wiki/start/topics/examples/x-accel/
            response = Response(
                headers={
                    'X-Accel-Redirect': _file.storage.url(relpath)
                }
            )
        return response

    @detail_route(methods=['get'], renderer_classes=(TemplateHTMLRenderer,))
    def xml(self, request, envelope_pk, pk):
        """
        Returns an evelope's metadata in XML format.
        """
        envelope = self.get_object()
        return Response(
            {'envelope': envelope},
            template_name='envelope_xml.html',
            content_type='text/xml'
        )

    @detail_route(methods=['get'])
    def qa_scripts(self, request, envelope_pk, pk):
        """
        Returns the list of available QA rules for a file's schema(s),
        as list of dicts with the keys:
            `id`
            `title`
            `last_updated`
            `max_size`
        """
        envelope_file = self.get_object()
        remote_qa = RemoteQA(
            envelope_file.envelope.obligation_spec.qa_xmlrpc_uri
        )

        scripts = []
        if envelope_file.xml_schema is not None:
            for schema in envelope_file.xml_schema.split(' '):
                scripts += remote_qa.get_scripts(schema)

        return Response(scripts)

    @detail_route(methods=['post'])
    def run_qa_script(self, request, envelope_pk, pk):
        """
        Runs the QA script with id POST-ed as ``script_id`` against the
        XML file, and returns the result as dict with the keys:
            `content-type`
            `result`
            `feedback_status`
            `feedback_message`
        """
        script_id = request.data.get('script_id')
        envelope_file = self.get_object()
        remote_qa = RemoteQA(
            envelope_file.envelope.obligation_spec.qa_xmlrpc_uri
        )
        # file_url = fully_qualify_url(envelope_file.get_api_download_url())
        file_url = fully_qualify_url(envelope_file.get_file_url())
        return Response(remote_qa.run_script(file_url, str(script_id)))

    @detail_route(methods=['get'])
    def feedback(self, request, envelope_pk, pk):
        """
        Returns the QA feedback, if any, for the envelope file.
        """
        envelope_file = self.get_object()
        qa_jobs = QAJob.objects.filter(completed=True, envelope_file=envelope_file)
        serializer = QAJobSerializer(qa_jobs, many=True, context={'request': request})
        return Response(serializer.data)

    @detail_route(methods=['get'])
    def conversion_scripts(self, request, envelope_pk, pk):
        """
        Returns the list of available conversion scripts for a file's schema(s),
        as list of dicts with the keys:
            `description`
            `content_type_out`
            `xml_schema`
            `result_type`
            `xsl'
            `convert_id`
        """
        envelope_file = self.get_object()
        remote_conversion = RemoteConversion(
            envelope_file.envelope.obligation_spec.qa_xmlrpc_uri
        )

        scripts = []
        if envelope_file.xml_schema is not None:
            for schema in envelope_file.xml_schema.split(' '):
                scripts += remote_conversion.get_conversions(schema)

        return Response(scripts)

    @detail_route(methods=['post'])
    def run_conversion_script(self, request, envelope_pk, pk):
        """
        Runs the conversion script with id POST-ed as ``convert_id`` against the
        XML file, and returns the result as dict with the keys:
            `content`
            `content-type`
            `filename`
        """
        script_id = request.data.get('convert_id')
        envelope_file = self.get_object()
        remote_conversion = RemoteConversion(
            envelope_file.envelope.obligation_spec.qa_xmlrpc_uri
        )
        # file_url = fully_qualify_url(envelope_file.get_api_download_url())
        file_url = fully_qualify_url(envelope_file.get_file_url())
        conversion_result = remote_conversion.convert_xml(file_url, str(script_id))

        response = HttpResponse()
        # force browser to download file
        response['Content-Disposition'] = f'attachment; filename={conversion_result["filename"]}'
        response['Content-Type'] = conversion_result["content-type"]
        response.write(conversion_result["content"].data)

        return response


class EnvelopeWorkflowViewSet(viewsets.ModelViewSet):
    queryset = BaseWorkflow.objects.all()
    serializer_class = NestedEnvelopeWorkflowSerializer
    permission_classes = (permissions.IsAuthenticated, )


class UploadTokenViewSet(viewsets.ModelViewSet):
    queryset = UploadToken.objects.all()
    serializer_class = NestedUploadTokenSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request, envelope_pk):
        """
        Creates an ``UploadToken`` for the envelope.
        Used by `tusd` uploads server for user/envelope correlation.
        Upload tokens cannot be issued for finalized envelopes.

        Returns::

            {
              'token': <base64 encoded token>
            }

        """
        envelope = Envelope.objects.get(pk=envelope_pk)

        if envelope.finalized:
            return Response(
                {'error': 'envelope is finalized'},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif not envelope.workflow.upload_allowed:
            return Response(
                {'error': 'envelope state does not allow uploads'},
                status=status.HTTP_400_BAD_REQUEST
            )

        token = envelope.upload_tokens.create(user=request.user)
        response = {
                'token': token.token
            }

        # Include base64 encoded token in development environments
        if settings.DEBUG:
            response['token_base64'] = b64encode(token.token.encode())

        return Response(response)

    def list(self, request, envelope_pk):
        """
        Returns the tokens issued for a given envelope.
        """
        queryset = UploadToken.objects.filter(envelope=envelope_pk)
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        return Response(serializer.data)


class UploadHookView(viewsets.ViewSet):
    """
    Handles upload notifications for tusd hooks:
        - ``pre-create``
        - ``post-create``
        - ``post-finish``
        - ``post-terminate``
        - ``post-receive``

    """

    @staticmethod
    def handle_pre_create(request):
        """
        Handles a pre-create notification from `tusd`.

        Sets the file name on the token.

        Returns an OK response only if:
         - the upload `token` the `MetaData` field is validated
         - the token's user is authenticated
         - a `filename` field is present in `MetaData`
        """

        info(f'UPLOAD pre-create: {request.data}')
        meta_data = request.data.get('MetaData', {})
        tok = meta_data.get('token', '')
        filename = meta_data.get('filename')
        try:
            token = UploadToken.objects.get(token=tok)

            if token.has_expired():
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

            if filename is None:
                error(f'UPLOAD denied on envelope "{token.envelope}" '
                      f'for "{token.user}": filename is missing')
                return Response(
                    {'error': 'filename not in MetaData'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not EnvelopeFile.has_valid_extension(filename, include_archives=True):
                error(f'UPLOAD denied on envelope "{token.envelope}" '
                      f'for "{token.user}": bad file extension')
                return Response(
                    {'error': 'bad file extension'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            token.filename = filename
            token.save()

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
        Sets the newly issued tus ID on the token.
        """
        info(f'UPLOAD post-create: {request.data}')
        meta_data = request.data.get('MetaData', {})
        tok = meta_data.get('token', '')
        try:
            token = UploadToken.objects.get(token=tok)
            token.tus_id = request.data.get('ID')
            token.save()
        except UploadToken.DoesNotExist:
            error('UPLOAD denied: INVALID TOKEN')
            return Response(
                {'error': 'invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response()

    @staticmethod
    def handle_post_finish(request):
        """
        Handles a post-finish notification from `tusd`.
        The uploaded file is used to create an EnvelopeFile, or replace its
        underlying file on disk if one with the same name exists.

        Archives (only ZIPs currently) are extracted *without* directory structure.
        If setting ``ARCHIVE_PATH_PREFIX`` is ``True`` (default), the files are saved with
        a prefix of '_'-separated path components, i.e. 'dir1/dir2/file.xml' becomes
        'dir1_dir2_file.xml'.
        """

        info(f'UPLOAD post-finish: {request.data}')
        meta_data = request.data.get('MetaData', {})
        tok = meta_data.get('token', '')
        # filename presence was enforced during pre-create
        file_name = meta_data['filename']
        file_ext = file_name.split('.')[-1].lower()

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

            upload_id = request.data.get('ID')

            file_path = os.path.join(
                settings.TUSD_UPLOADS_DIR,
                f'{upload_id}.bin'
            )

            file_info_path = os.path.join(
                settings.TUSD_UPLOADS_DIR,
                f'{upload_id}.info'
            )

            file_path = Path(file_path).resolve()
            file_info_path = Path(file_info_path).resolve()

            for f in (file_path, file_info_path):
                if not f.is_file():
                    raise FileNotFoundError(f'UPLOAD tusd file not found: {f}')

            # Regular files
            if file_ext not in settings.ALLOWED_UPLOADS_ARCHIVE_EXTENSIONS:
                envelope_file, is_new = EnvelopeFile.get_or_create(
                    token.envelope,
                    file_name
                )
                if not is_new:
                    token.envelope.delete_disk_file(file_name)

                envelope_file.file.save(file_name, File(file_path.open()))
                if file_ext == 'xml':
                    envelope_file.xml_schema = envelope_file.extract_xml_schema()

                envelope_file.uploader = token.user
                envelope_file.save()
            # Archives, currently zip only
            elif file_ext == 'zip':
                try:
                    with ZipFile(file_path) as up_zip:
                        for zip_member in up_zip.namelist():
                            member_info = up_zip.getinfo(zip_member)
                            # Skip directories and files with non-allowed extensions
                            if member_info.is_dir() or not EnvelopeFile.has_valid_extension(member_info.filename):
                                continue
                            if not settings.ARCHIVE_PATH_PREFIX:
                                member_name = os.path.basename(zip_member)
                            else:
                                member_name = '_'.join([p.replace(' ', '') for p in path_parts(zip_member)])
                            member_ext = member_name.split('.')[-1].lower()
                            envelope_file, is_new = EnvelopeFile.get_or_create(
                                token.envelope,
                                member_name
                            )
                            if not is_new:
                                token.envelope.delete_disk_file(member_name)

                            with up_zip.open(zip_member) as member_file:
                                envelope_file.file.save(member_name, member_file)
                                if member_ext == 'xml':
                                    envelope_file.xml_schema = envelope_file.extract_xml_schema()

                                envelope_file.uploader = token.user
                                envelope_file.save()

                except BadZipFile:
                    error(f'UPLOAD Bad ZIP file: "{file_path}"')
                    return Response(
                        {'error': 'bad zip file'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Finally, remove the token and the tusd files pair
            token.delete()
            file_path.unlink()
            file_info_path.unlink()

        except UploadToken.DoesNotExist:
            error(f'UPLOAD denied on envelope "{token.envelope}" '
                  f'for "{token.user}": INVALID TOKEN')
            return Response(
                {'error': 'invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except FileNotFoundError as err:
            error(f'{err}')
            return Response(
                {'error': 'file not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response()

    @staticmethod
    def handle_post_terminate(request):
        """
        Handles a post-terminate notification from `tusd`.
        Deletes the token issued for the upload.
        """
        info(f'UPLOAD post-terminate: {request.data}')
        meta_data = request.data.get('MetaData', {})
        tok = meta_data.get('token', '')
        try:
            token = UploadToken.objects.get(token=tok)
            token.delete()
        except UploadToken.DoesNotExist:
            warn('UPLOAD could not find token to delete on post-terminate.')
        return Response()

    def create(self, request):
        """
        Dispatches notifications from `tusd` to appropriate handler.
        """
        # Original header name sent by tusd is `Hook-Name`, Django mangles it
        hook_name = self.request.META.get('HTTP_HOOK_NAME')
        try:
            hook_handler = getattr(self, f'handle_{hook_name.replace("-", "_")}')
        except AttributeError:
            return Response(
                {'hook_not_supported': hook_name},
                status=status.HTTP_400_BAD_REQUEST
            )

        return hook_handler(request)
