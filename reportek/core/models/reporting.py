import os
import logging
from django.conf import settings
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _
from edw.djutils import protected
from model_utils import FieldTracker
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .workflows import (
    BaseWorkflow,
)

from .rod import (
    Reporter,
    ReporterSubdivision,
    Obligation,
    ObligationSpec,
    ReportingCycle
)

from .qa import QAJob, QAJobResult

from reportek.core.utils import (
    get_xsd_uri,
    fully_qualify_url,
)

log = logging.getLogger('reportek.workflows')
info = log.info
debug = log.debug
warn = log.warning
error = log.error


ENVELOPE_ROOT_DIR = 'envelopes'

UPLOAD_TOKEN_LENGTH = 64
UPLOAD_TOKEN_DURATION = 60 * 60  # 60 minutes

__all__ = [
    'Envelope',
    'EnvelopeFile',
    'EnvelopeOriginalFile',
    'EnvelopeSupportFile',
    'EnvelopeLink',
    'UploadToken'
]


class EnvelopeQuerySet(models.QuerySet):
    pass


class EnvelopeManager(models.Manager.from_queryset(EnvelopeQuerySet)):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'reporter',
            'obligation_spec',
            'reporting_cycle',
            'workflow'
        )


class Envelope(models.Model):
    name = models.CharField(max_length=256)

    description = models.TextField(null=True, blank=True)
    coverage_note = models.CharField(max_length=256, null=True, blank=True)

    reporter = models.ForeignKey(Reporter, related_name='envelopes')
    obligation_spec = models.ForeignKey(ObligationSpec, related_name='envelopes')
    reporter_subdivision = models.ForeignKey(ReporterSubdivision,
                                             blank=True, null=True,
                                             related_name='envelopes')
    reporting_cycle = models.ForeignKey(ReportingCycle, related_name='envelopes')

    workflow = models.OneToOneField(BaseWorkflow,
                                    on_delete=models.CASCADE,
                                    related_name='envelope',
                                    null=True, blank=True)

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
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
        return reverse('api:envelope-detail',
                       kwargs={'pk': self.pk})

    @property
    def fq_url(self):
        return fully_qualify_url(self.url)

    @property
    def auto_qa_jobs(self):
        """
        The envelope's most recent QA job for each file.
        """
        return [
            job
            for file in self.files.all()
            for job in file.qa_jobs.all()
        ]

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
        return [
            result
            for file in self.files.all()
            for result in file.qa_results
        ]

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

        return os.path.join(ENVELOPE_ROOT_DIR,
                            year, reporter, spec, envelope)

    def delete_disk_file(self, file_name):
        """
        Used to delete an existing envelope file from disk, to avoid
        auto-renaming in `Storage.get_available_name` during
        `EnvelopeFile.file.save()`.
        """
        env_file = os.path.join(
            settings.PROTECTED_ROOT,
            self.get_storage_directory(),
            file_name
        )
        debug(f'Deleting envelope file: {env_file}')
        try:
            os.remove(env_file)
        except FileNotFoundError:
            warn(f'Could not find envelope file "{env_file}"')


# TODO: move me somewhere nice (and improve me)
def validate_filename(value):
    if os.path.basename(os.path.join('test', value)) != value:
        raise ValidationError(
            _("'%(value)s' is not a valid file name"),
            params={'value': value},
        )


class EnvelopeFileQuerySet(models.QuerySet):

    def delete(self):
        for obj in self:
            try:
                os.remove(obj.file.path)
                debug(f'Deleted disk file {obj.file.path}')
            except FileNotFoundError:
                error(f'Could not delete envelope file from disk (not found): '
                      f'{obj.file.path}')
        super().delete()


class BaseEnvelopeFile(models.Model):
    """
    Abstract base class for EnvelopeFile and EnvelopeOriginalFile,
    holding some common fields for these two.
    """

    class Meta:
        abstract = True
        unique_together = ('envelope', 'name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # keep track of the name to handle renames
        self._prev_name = (None if self.pk is None
                           else self.name)

    def get_envelope_directory(self, filename):
        return os.path.join(
            self.envelope.get_storage_directory(),
            os.path.basename(filename)
        )

    # Used by get_download_url()
    _download_view_name = ''

    # Used by subclasses to properly name related names, events etc
    _class_specifier = ''

    file = protected.fields.ProtectedFileField(upload_to=get_envelope_directory,
                                               max_length=512)
    # initially derived from the filename, a change triggers rename
    name = models.CharField(max_length=256, validators=[validate_filename])

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    restricted = models.BooleanField(default=False)

    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True
    )

    objects = EnvelopeFileQuerySet.as_manager()

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
        return reverse(self._download_view_name, kwargs={
            'envelope_pk': self.envelope_id,
            'pk': self.pk,
        })

    def __repr__(self):
        return '<%s: %s/%s>' % (self.__class__.__name__,
                                self.envelope.pk,
                                self.name)

    @classmethod
    def get_or_create(cls, envelope, file_name):
        """
        Locates an `EnvelopeFile` based on `file_name`, or creates a new one.
        Returns a tuple of the `EnvelopeFile` instance and a boolean indicating
        if it is newly created.
        """
        is_new = True
        try:
            obj = cls.objects.get(
                envelope=envelope,
                name=file_name
            )
            is_new = False

        except cls.DoesNotExist:
            obj = cls(envelope=envelope, name=file_name)

        return obj, is_new

    def save(self, *args, **kwargs):
        # don't allow any operations on a final envelope
        if self.envelope.finalized:
            raise RuntimeError("Envelope is final.")

        renamed = False
        new = False
        if self.pk is None:
            new = True
            self.name = os.path.basename(self.file.name)
            # TODO: go full OCD and guard against receiving both name and file?
        elif self.name != self._prev_name:
            renamed = True

        if renamed:
            # WARNING, WARNING, WARNING:
            # validations aren't performed at save, because django.
            # forms and drf *will* validate, but if data might come in
            # in other ways... warning!!! !! !!

            old_name = self.file.name
            new_name = os.path.join(os.path.dirname(old_name),
                                    self.name)

            old_path = self.file.path
            new_path = os.path.join(os.path.dirname(old_path),
                                    self.name)

            self.file.name = new_name
        else:
            new_path = old_path = self.file.path

        debug(f'saving file name: {self.file.name}')
        # save first to catch data integrity errors.
        # TODO: wrap this in a transaction with below, who knows
        # how that might fail...
        super().save(*args, **kwargs)

        # and rename on disk
        if renamed:
            debug(f'renaming: {old_path} to {new_path}')
            os.rename(old_path, new_path)

        channel_layer = get_channel_layer()
        payload = {
            'file_id': self.pk,
        }

        if new:
            async_to_sync(channel_layer.group_send)(
                self.envelope.channel,
                {
                    'type': f'envelope.added_{self._class_specifier}',
                    'data': payload
                }
            )
        else:
            async_to_sync(channel_layer.group_send)(
                self.envelope.channel,
                {
                    'type': f'envelope.changed_{self._class_specifier}',
                    'data': payload
                }
            )

    def delete(self, *args, **kwargs):
        try:
            os.remove(self.file.path)
            debug(f'Deleted disk file {self.file.path}')
        except FileNotFoundError:
            error(f'Could not delete envelope {self._class_specifier} from disk (not found): '
                  f'{self.file.path}')

        channel = self.envelope.channel
        file_id = self.pk
        super().delete(*args, **kwargs)

        channel_layer = get_channel_layer()
        payload = {
            'file_id': file_id,
        }

        async_to_sync(channel_layer.group_send)(
            channel,
            {
                'type': f'envelope.deleted_{self._class_specifier}',
                'data': payload
            }
        )


class EnvelopeOriginalFile(BaseEnvelopeFile):
    """
    Used to describe original non-XML files uploaded to the envelope
    that are converted to and stored as XML EnvelopeFiles.
    """

    class Meta(BaseEnvelopeFile.Meta):
        db_table = 'core_envelope_original_file'

    # Overriding so get_download_url() works
    _download_view_name = 'api:envelope-original-file-download'

    # Overriding so notifications work
    _class_specifier = 'original_file'

    envelope = models.ForeignKey(Envelope, related_name=f'{_class_specifier}s')


class EnvelopeFile(BaseEnvelopeFile):

    class Meta(BaseEnvelopeFile.Meta):
        db_table = 'core_envelope_file'

    # Overriding so get_download_url() works
    _download_view_name = 'api:envelope-file-download'

    # Overriding so notifications work
    _class_specifier = 'file'

    envelope = models.ForeignKey(Envelope, related_name=f'{_class_specifier}s')

    xml_schema = models.CharField(max_length=200, blank=True, null=True)

    original_file = models.ForeignKey(EnvelopeOriginalFile,
                                      related_name='envelope_files',
                                      null=True)

    @property
    def qa_results(self):
        try:
            return QAJobResult.objects.filter(job__in=self.qa_jobs.all()).all()
        except QAJobResult.DoesNotExist:
            return None

    @staticmethod
    def has_valid_extension(filename, include_archives=False, include_spreadsheets=False):
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


class EnvelopeSupportFile(BaseEnvelopeFile):
    """
    Files uploaded to the envelope as support information (e.g. PDFs)
    """

    class Meta(BaseEnvelopeFile.Meta):
        db_table = 'core_envelope_support_file'

    # Overriding so get_download_url() works
    _download_view_name = 'api:envelope-support-file-download'

    # Overriding so notifications work
    _class_specifier = 'support_file'

    envelope = models.ForeignKey(Envelope, related_name=f'{_class_specifier}s')


class EnvelopeLink(models.Model):
    envelope = models.ForeignKey(Envelope, on_delete=models.CASCADE, related_name='links')
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
        Envelope,
        related_name='upload_tokens',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='upload_tokens',
        on_delete=models.CASCADE
    )
    token = models.CharField(
        max_length=100, db_index=True,
        unique=True, default=default_token
    )

    filename = models.CharField(max_length=256)
    tus_id = models.CharField(max_length=32, blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(default=token_valid_until)

    class Meta:
        db_table = 'core_upload_token'
        ordering = ('-created_at',)

    def __str__(self):
        return f'Upload token for user "{self.user}" ' \
               f'on envelope "{self.envelope}"'

    def has_expired(self):
        return self.valid_until < (
            timezone.now() + timezone.timedelta(seconds=self.GRACE_SECONDS))
