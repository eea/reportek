import os
import logging
from django.conf import settings
from django.db import models, transaction
from django.db.models.signals import post_save
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _
from typedmodels.models import TypedModel
from model_utils import FieldTracker, Choices
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .workflows import (BaseWorkflow,)

from .rod import (
    Reporter, ReporterSubdivision, Obligation, ObligationSpec, ReportingCycle
)

from .qa import QAJob, QAJobResult
from ..conversion import RemoteConversion

from reportek.core.utils import (get_xsd_uri, fully_qualify_url)

log = logging.getLogger('reportek.workflows')
info = log.info
debug = log.debug
warn = log.warning
error = log.error


ENVELOPE_ROOT_DIR = 'envelopes'

UPLOAD_TOKEN_LENGTH = 64
UPLOAD_TOKEN_DURATION = 60 * 60  # 60 minutes

__all__ = [
    'Envelope', 'EnvelopeFile', 'EnvelopeSupportFile', 'EnvelopeLink', 'UploadToken'
]


class EnvelopeQuerySet(models.QuerySet):
    pass


class EnvelopeManager(models.Manager.from_queryset(EnvelopeQuerySet)):

    def get_queryset(self):
        return super().get_queryset().select_related(
            'reporter', 'obligation_spec', 'reporting_cycle', 'workflow'
        )


class Envelope(models.Model):
    name = models.CharField(max_length=256)

    description = models.TextField(null=True, blank=True)
    coverage_note = models.CharField(max_length=256, null=True, blank=True)

    # TODO: Review on_delete policy when implementing ROD integration
    reporter = models.ForeignKey(Reporter, related_name='envelopes', on_delete=models.PROTECT)
    obligation_spec = models.ForeignKey(ObligationSpec, related_name='envelopes', on_delete=models.PROTECT)
    reporter_subdivision = models.ForeignKey(
        ReporterSubdivision, blank=True, null=True, related_name='envelopes', on_delete=models.PROTECT
    )
    reporting_cycle = models.ForeignKey(ReportingCycle, related_name='envelopes', on_delete=models.PROTECT)

    workflow = models.OneToOneField(
        BaseWorkflow,
        on_delete=models.PROTECT,
        related_name='envelope',
        null=True,
        blank=True,
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    finalized = models.BooleanField(default=False)

    objects = EnvelopeManager()
    tracker = FieldTracker()

    @property
    def obligation(self):
        if self.obligation_spec is None:
            return None

        return self.obligation_spec.obligation

    @property
    def is_assigned(self):
        return self.assigned_to is not None

    @property
    def url(self):
        return reverse('api:envelope-detail', kwargs={'pk': self.pk})

    @property
    def fq_url(self):
        return fully_qualify_url(self.url)

    @property
    def auto_qa_jobs(self):
        """
        The envelope's most recent QA job for each file.
        """
        return [job for file in self.files.all() for job in file.qa_jobs.all()]

    @property
    def auto_qa_complete(self):
        """
        Is `True` when every QA job on the envelope's files is complete.
        The most recent QA job per file is considered.
        """
        return all([job.completed for job in self.auto_qa_jobs])

    @property
    def auto_qa_results(self):
        """
        Latest QA job results for the envelope's files.
        """
        return [result for file in self.files.all() for result in file.qa_results]

    @property
    def auto_qa_ok(self):
        return self.auto_qa_complete and all([r.ok for r in self.auto_qa_results])

    @property
    def channel(self):
        """The envelope's WebSocket channel name"""
        return f'envelope_{self.pk}'

    def __str__(self):
        return self.name

    def handle_auto_qa_results(self):
        return self.workflow.handle_auto_qa_results()

    def save(self, *args, **kwargs):
        # don't allow any operations on a final envelope
        if self.tracker.changed() and self.tracker.previous('finalized'):
            raise RuntimeError("Envelope is final.")

        # On first save:
        if not self.pk or kwargs.get('force_insert', False):
            # - import the workflow class set on the envelope's obligation spec
            wf_path_components = self.obligation_spec.workflow_class.split('.')
            module_name = '.'.join(wf_path_components[:-1])
            class_name = wf_path_components[-1]
            module = __import__(module_name, fromlist=[class_name])
            # Instantiate a new workflow and set it on the envelope
            wf_class = getattr(module, class_name)
            workflow = wf_class(name=f'Envelope "{self.name}"\'s workflow')
            workflow.save()
            self.workflow = workflow

        if self.reporter_subdivision is not None:
            if self.reporter_subdivision.reporter != self.reporter:
                raise RuntimeError('Envelope subdivision must match reporter!')

        super().save(*args, **kwargs)

    def get_storage_directory(self):
        # generate a multi-level, stable path:
        # reporting year / reporter / obligation spec / envelope id

        year = str(self.created_at.year)
        reporter = self.reporter.abbr
        spec = str(self.obligation_spec_id)
        envelope = str(self.id)

        return os.path.join(ENVELOPE_ROOT_DIR, year, reporter, spec, envelope)

    def delete_disk_file(self, file_name):
        """
        Used to delete an existing envelope file from disk, to avoid
        auto-renaming in `Storage.get_available_name` during
        `EnvelopeFile.file.save()`.
        """
        env_file = os.path.join(
            settings.PROTECTED_ROOT, self.get_storage_directory(), file_name
        )
        debug(f'Deleting envelope file: {env_file}')
        try:
            os.remove(env_file)
        except FileNotFoundError:
            warn(f'Could not find envelope file "{env_file}"')


class EnvelopeFileQuerySet(models.QuerySet):

    def delete(self):
        for obj in self:
            try:
                os.remove(obj.file.path)
                debug(f'Deleted disk file {obj.file.path}')
            except FileNotFoundError:
                error(
                    f'Could not delete envelope file from disk (not found): '
                    f'{obj.file.path}'
                )
        super().delete()

    def get_or_create(self, **kwargs):
        if 'file' in kwargs and 'envelope' in kwargs:
            envelope = kwargs['envelope']
            if not isinstance(envelope, Envelope):
                envelope = Envelope.objects.get(pk=envelope)
            kwargs['file'] = f'{envelope.get_storage_directory()}/{kwargs["file"]}'
        return super().get_or_create(**kwargs)


class OverwriteFileSystemStorage(FileSystemStorage):
    """
    Removes the existing file when checked during `get_or_create`
    """

    def __init__(self):
        # Keep the explicit location out of migrations
        super().__init__(location=str(settings.PROTECTED_ROOT))

    def get_available_name(self, name, max_length=None):
        if self.exists(name):
            print(f'Removing old file {name}...')
            os.remove(os.path.join(self.location, name))
            return name

        return super().get_available_name(name, max_length)


EnvelopeFileStorage = OverwriteFileSystemStorage()


class BaseEnvelopeFile(TypedModel):
    """
    Abstract base class for EnvelopeFile and EnvelopeOriginalFile,
    holding some common fields for these two.
    """

    CONVERSION_STATUS = Choices(
        (-1, 'error', _('error')),
        (0, 'na', _('na')),
        (1, 'running', _('running')),
        (2, 'finished', _('finished')),
    )

    class Meta:
        db_table = 'core_envelope_file'
        unique_together = ('envelope', 'file')

    def get_envelope_directory(self, filename):
        return os.path.join(
            self.envelope.get_storage_directory(), os.path.basename(filename)
        )

    envelope = models.ForeignKey(Envelope, related_name=f'files', on_delete=models.CASCADE)

    file = models.FileField(
        upload_to=get_envelope_directory, max_length=512, storage=EnvelopeFileStorage
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    restricted = models.BooleanField(default=False)

    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )

    is_support = models.BooleanField(default=False)

    original_file = models.ForeignKey(
        'self',
        related_name='converted_files',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    conversion_status = models.IntegerField(
        choices=CONVERSION_STATUS, default=CONVERSION_STATUS.na
    )

    objects = EnvelopeFileQuerySet.as_manager()
    tracker = FieldTracker()

    @property
    def name(self):
        return os.path.basename(self.file.name)

    @property
    def extension(self):
        return self.name.split('.')[-1].lower()

    @property
    def size(self):
        return self.file.size

    @property
    def download_url(self):
        return self.get_download_url()

    @property
    def fq_download_url(self):
        return fully_qualify_url(self.download_url)

    def get_download_url(self):
        return reverse(
            'api:envelope-file-download',
            kwargs={'envelope_pk': self.envelope_id, 'pk': self.pk},
        )

    def __repr__(self):
        return '<%s: %s/%s>' % (self.__class__.__name__, self.envelope.pk, self.name)

    def save(self, *args, **kwargs):
        # don't allow any operations on a final envelope
        if self.envelope.finalized:
            raise RuntimeError('Envelope is final.')

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        try:
            os.remove(self.file.path)
            debug(f'Deleted disk file {self.file.path}')
        except FileNotFoundError:
            error(
                f'Could not delete envelope file from disk (not found): '
                f'{self.file.path}'
            )

        channel = self.envelope.channel
        file_id = self.pk
        super().delete(*args, **kwargs)

        channel_layer = get_channel_layer()
        payload = {'file_id': file_id}

        async_to_sync(channel_layer.group_send)(
            channel, {'type': 'envelope.deleted_file', 'data': payload}
        )


class EnvelopeFile(BaseEnvelopeFile):

    @staticmethod
    def has_valid_extension(
        filename, include_archives=False, include_spreadsheets=False
    ):
        """
        Checks a file's extension against allowed extensions.
        If `include_archives` is `True`, extensions in
        `ALLOWED_UPLOADS_ARCHIVE_EXTENSIONS` are permitted.
        """
        allowed_extensions = settings.ALLOWED_UPLOADS_EXTENSIONS
        if include_archives:
            allowed_extensions = allowed_extensions + settings.ALLOWED_UPLOADS_ARCHIVE_EXTENSIONS
        if include_spreadsheets:
            allowed_extensions = allowed_extensions + settings.ALLOWED_UPLOADS_ORIGINAL_EXTENSIONS
        return filename.split('.')[-1].lower() in allowed_extensions

    def extract_xml_schema(self):
        return get_xsd_uri(self.file.path)

    @property
    def qa_results(self):
        try:
            return QAJobResult.objects.filter(job__in=self.qa_jobs.all()).all()

        except QAJobResult.DoesNotExist:
            return None

    def convert_to_xml(self):
        if self.extension == 'xml':
            raise RuntimeError('Cannot convert - file is already XML!')

        self.conversion_status = self.CONVERSION_STATUS.running
        self.save()

        debug(f'Starting conversion to XML for {self.name}')
        remote_conversion = RemoteConversion(
            self.envelope.obligation_spec.qa_xmlrpc_uri
        )
        result = remote_conversion.convert_spreadsheet_to_xml(self.fq_download_url)

        if result.get('resultCode', 'ERROR') != '0':
            warn(f'Conversion to XML failed for {self.name}')
            self.conversion_status = self.CONVERSION_STATUS.error
            self.save()
            return

        with transaction.atomic():
            # Save every XML file resulted from the original's conversion
            for converted_content in result.get('convertedFiles', []):
                debug(f'Saving converted file {converted_content["fileName"]}')
                converted_file, is_new = self.objects.get_or_create(
                    envelope=self.envelope, name=converted_content['fileName']
                )
                if not is_new:
                    self.envelope.delete_disk_file(converted_content['fileName'])
                converted_file.file.save(
                    converted_file.name, ContentFile(converted_content['content'].data)
                )

                if converted_file.extension == 'xml':
                    converted_file.xml_schema = converted_file.extract_xml_schema()

                converted_file.uploader = self.uploader
                converted_file.original_file = self
                converted_file.save()

            self.conversion_status = self.CONVERSION_STATUS.finished
            self.save()


def after_file_save(sender, instance, created, **kwargs):
    """
    Trigger conversion to XML after saving uploaded file.
    Only (hopefully) has effect if the file has changed.
    """
    channel_layer = get_channel_layer()
    payload = {'file_id': instance.pk}

    if created:
        async_to_sync(channel_layer.group_send)(
            instance.envelope.channel, {'type': 'envelope.added_file', 'data': payload}
        )
    else:
        async_to_sync(channel_layer.group_send)(
            instance.envelope.channel,
            {'type': 'envelope.changed_file', 'data': payload},
        )

    if instance.tracker.has_changed('file') and instance.extension != 'xml':
        instance.convert_to_xml()


post_save.connect(after_file_save, sender=EnvelopeFile)


class EnvelopeSupportFile(BaseEnvelopeFile):
    pass


class EnvelopeLink(models.Model):
    envelope = models.ForeignKey(
        Envelope, on_delete=models.CASCADE, related_name='links'
    )
    link = models.URLField(max_length=500)
    text = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        db_table = 'core_envelope_link'
        unique_together = ('envelope', 'link')


def default_token():
    return get_random_string(UPLOAD_TOKEN_LENGTH)


def token_valid_until():
    return timezone.now() + timezone.timedelta(seconds=UPLOAD_TOKEN_DURATION)


class UploadToken(models.Model):

    GRACE_SECONDS = 30

    envelope = models.ForeignKey(
        Envelope, related_name='upload_tokens', on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='upload_tokens', on_delete=models.CASCADE
    )
    token = models.CharField(
        max_length=100, db_index=True, unique=True, default=default_token
    )

    filename = models.CharField(max_length=256)
    tus_id = models.CharField(max_length=32, blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(default=token_valid_until)

    class Meta:
        db_table = 'core_upload_token'
        ordering = ('-created_at',)

    def __str__(self):
        return f'Upload token for user "{self.user}" ' f'on envelope "{self.envelope}"'

    def has_expired(self):
        return self.valid_until < (
            timezone.now() + timezone.timedelta(seconds=self.GRACE_SECONDS)
        )
