import os
import logging
from django.conf import settings
from django.db import models, transaction
from django.db.models.signals import post_save
from django.db.models.aggregates import Count
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from model_utils import FieldTracker, Choices
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .mixins import ValidateOnSaveMixin
from .utils import PaginatedRawQuerySet
from .workflows import (BaseWorkflow,)

from .rod import (
    Reporter, ReporterSubdivision, Obligation, ObligationSpec,
    ObligationSpecReporter, ReportingCycle
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
    'Envelope',
    'EnvelopeObligationSpec',
    'DataFile',
    'SupportFile',
    'Link',
    'UploadToken',
]


class EnvelopeQuerySet(models.QuerySet):
    pass


class EnvelopeManager(models.Manager.from_queryset(EnvelopeQuerySet)):

    def get_queryset(self):
        return super().get_queryset().select_related(
            'reporter', 'workflow'
        ).prefetch_related(
            'obligation_specs'
        )

    def raw(self, raw_query, params=None, translations=None, using=None):
        if using is None:
            using = self.db
        return PaginatedRawQuerySet(
            raw_query, model=self.model, params=params, translations=translations, using=using
        )


class Envelope(ValidateOnSaveMixin, models.Model):

    COVERAGE_INTERVAL_CHOICE = Choices(
        (0, 'whole_year', _('Whole year')),
        (1, 'first_half', _('First half')),
        (2, 'second_half', _('Second half')),
        (3, 'first_quarter', _('First quarter')),
        (4, 'second_quarter', _('Second quarter')),
        (5, 'third_quarter', _('Third quarter')),
        (6, 'fourth_quarter', _('Fourth quarter')),
        (7, 'jan', _('January')),
        (8, 'feb', _('February')),
        (9, 'mar', _('March')),
        (10, 'apr', _('April')),
        (11, 'may', _('May')),
        (12, 'jun', _('June')),
        (13, 'jul', _('July')),
        (14, 'aug', _('August')),
        (15, 'sep', _('September')),
        (16, 'oct', _('October')),
        (17, 'nov', _('November')),
        (18, 'dec', _('December')),
    )

    name = models.CharField(max_length=256)

    description = models.TextField(null=True, blank=True)
    coverage_note = models.CharField(max_length=256, null=True, blank=True)

    # TODO: Review on_delete policy when implementing ROD integration
    reporter = models.ForeignKey(
        Reporter, related_name='envelopes', on_delete=models.PROTECT
    )

    obligation_specs = models.ManyToManyField(
        ObligationSpec, through='core.EnvelopeObligationSpec'
    )

    reporter_subdivision = models.ForeignKey(
        ReporterSubdivision,
        blank=True,
        null=True,
        related_name='envelopes',
        on_delete=models.PROTECT,
    )

    coverage_start_year = models.IntegerField(null=True, blank=True)
    coverage_end_year = models.IntegerField(null=True, blank=True)
    coverage_interval = models.IntegerField(
        null=True, blank=True, choices=COVERAGE_INTERVAL_CHOICE
    )

    workflow = models.OneToOneField(
        BaseWorkflow,
        on_delete=models.PROTECT,
        related_name='envelope',
        null=True,
        blank=True,
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    finalized = models.BooleanField(default=False)

    objects = EnvelopeManager()
    tracker = FieldTracker()

    class Meta:
        ordering = ('created',)

    @property
    def obligations(self):
        return Obligation.objects.filter(pk__in=[s.obligation_id for s in self.obligation_specs.all()])

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
        return [job for file in self.datafiles.all() for job in file.qa_jobs.all()]

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
        return [result for file in self.datafiles.all() for result in file.qa_results]

    @property
    def auto_qa_ok(self):
        return self.auto_qa_complete and all([r.ok for r in self.auto_qa_results])

    @transaction.atomic
    def delete_qa_results(self, force=False):
        """
        Removes the `QAJob`s and corresponding `QAJobResult`s for the envelope's files.
        Unless `force` is `True`, this will not be done while there are unfinished QA
        jobs.
        """
        for f in self.files:
            f.delete_qa_results(force=force)

    @property
    def channel(self):
        """The envelope's WebSocket channel name"""
        return f'envelope_{self.pk}'

    @cached_property
    def storage_path(self):
        """
        Generates a multi-level, stable path for the envelope:
        envelope creation year / reporter id / envelope id /
        """
        year = str(self.created.year)
        reporter = str(self.reporter.pk)
        envelope = str(self.pk)

        return os.path.join(ENVELOPE_ROOT_DIR, year, reporter, envelope)

    @cached_property
    def data_files_path(self):
        return os.path.join(self.storage_path, 'data_files')

    @cached_property
    def support_files_path(self):
        return os.path.join(self.storage_path, 'support_files')

    @cached_property
    def system_user(self):
        User = get_user_model()
        try:
            return User.objects.get(username='system')

        except User.DoesNotExists:
            return None

    def __str__(self):
        return self.name

    def handle_auto_qa_results(self):
        return self.workflow.handle_auto_qa_results()

    def clean(self):
        if self.tracker.changed() and self.tracker.previous('finalized'):
            raise ValidationError(_('Finalized envelopes cannot be changed'))

        if self.reporter_subdivision is not None:
            if self.reporter_subdivision.reporter != self.reporter:
                raise ValidationError(
                    {
                        'reporter_subdivision': _(
                            'Envelope subdivision must match reporter!'
                        )
                    }
                )

        # Switch start/end coverage years if reversed
        if (
            self.coverage_start_year is not None
            and self.coverage_end_year is not None
            and self.coverage_start_year < self.coverage_end_year
        ):
            self.coverage_start_year, self.coverage_end_year = self.coverage_end_year, self.coverage_start_year

    # def save(self, *args, **kwargs):
    #     # On first save, instantiate a new workflow and set it on the envelope
    #     if self._state.adding:
    #         wf_class = self.obligation_specs.first().obligation_spec.workflow_cls()
    #         workflow = wf_class(name=f'Envelope "{self.name}"\'s workflow')
    #         workflow.save()
    #         self.workflow = workflow
    #
    #     super().save(*args, **kwargs)

    def delete_disk_file(self, file_name):
        """
        Used to delete an existing envelope file from disk, to avoid
        auto-renaming in `Storage.get_available_name` during
        `EnvelopeFile.file.save()`.
        """
        env_file = os.path.join(settings.PROTECTED_ROOT, self.storage_path, file_name)
        debug(f'Deleting envelope file: {env_file}')
        try:
            os.remove(env_file)
        except FileNotFoundError:
            warn(f'Could not find envelope file "{env_file}"')

    def assign_to_system(self):
        info(f'Assigning envelope "{self.name}" to SYSTEM')
        self.assigned_to = self.system_user
        self.save()


class EnvelopeObligationSpec(models.Model):

    envelope = models.ForeignKey(Envelope, on_delete=models.CASCADE)
    obligation_spec = models.ForeignKey(ObligationSpec, on_delete=models.PROTECT)
    reporting_cycle = models.ForeignKey(ReportingCycle, on_delete=models.PROTECT)

    class Meta:
        unique_together = ('envelope', 'obligation_spec')

    def __str__(self):
        return f'EnvelopeObligationSpec(envelope={self.envelope.pk}, ' \
               f'obligation_spec={self.obligation_spec.pk}), ' \
               f'reporting_cycle={self.reporting_cycle.pk})'

    def save(self, *args, **kwargs):
        if self._state.adding:
            another_spec = self.__class__.objects.filter(envelope=self.envelope).first()
            if another_spec is not None \
                and another_spec.obligation_spec.workflow_class != self.obligation_spec.workflow_class:

                raise RuntimeError(
                    'All obligation specs on an envelope must have the same workflow'
                )

            if self.envelope.reporter not in self.obligation_spec.reporters.all():
                raise RuntimeError(
                    f'Envelope reporter is not mapped to obligation spec {self.obligation_spec}'
                )

            reporter_mapping = ObligationSpecReporter.objects.filter(
                spec=self.obligation_spec, reporter=self.envelope.reporter
            ).first()

            other_spec_mappings = self.__class__.objects.filter(envelope=self.envelope)

            for spec_map in other_spec_mappings.all():
                if ObligationSpecReporter.objects.filter(
                    spec=spec_map.obligation_spec, reporter=self.envelope.reporter
                ).exclude(
                    subdivision_category=reporter_mapping.subdivision_category
                ).exists():
                    raise RuntimeError(
                        'All obligation specs on an envelope must have the same subdivision category (or none)'
                    )

        super().save(*args, **kwargs)

        print(self)
        # Instantiate envelope's workflow
        if self.envelope.workflow is None:
            wf_class = self.obligation_spec.workflow_cls
            workflow = wf_class(name=f'Envelope "{self.envelope.name}"\'s workflow')
            workflow.save()
            self.envelope.workflow = workflow
            self.envelope.save()


class BaseEnvelopeFileQuerySet(models.QuerySet):

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

    @staticmethod
    def process_kwargs(kwargs, envelope_path_attr):
        """
        Prepends the envelope file-specific path to the get_or_create file,
        when used with (envelope, file) named arguments to check for re-uploads.
        """
        if all(k in kwargs for k in ('envelope', 'file')):
            envelope = kwargs['envelope']
            if not isinstance(envelope, Envelope):
                envelope = Envelope.objects.get(pk=envelope)
            kwargs['file'] = f'{getattr(envelope, envelope_path_attr)}/{kwargs["file"]}'
        return kwargs


class OverwriteFileSystemStorage(FileSystemStorage):
    """
    Overwrites files instead of generating unique names.
    Existing files are removed during the check for available names.
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


def get_upload_path(instance, file_name):
    return instance.get_upload_path(file_name)


class BaseEnvelopeFile(models.Model):
    """
    Abstract base class for EnvelopeFile and EnvelopeSupportFile,
    holding some common fields for these two.
    """

    # Used when building envelope channel notification type names.
    # Set this to an appropriate name in the concrete class (e.g. 'file', 'support_file')
    channel_qualifier = None

    class Meta:
        abstract = True
        unique_together = ('envelope', 'file')

    envelope = models.ForeignKey(
        Envelope, related_name='%(class)ss', on_delete=models.CASCADE
    )

    file = models.FileField(
        upload_to=get_upload_path, max_length=512, storage=EnvelopeFileStorage
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    restricted = models.BooleanField(default=False)

    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )

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
        raise NotImplementedError(
            'get_download_url must be implemented by each concrete class'
        )

    def get_upload_path(self, file_name):
        raise NotImplementedError(
            'get_upload_path must be implemented by each concrete class'
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
            channel,
            {'type': f'envelope.deleted_{self.channel_qualifier}', 'data': payload},
        )


def after_file_save(sender, instance, created, **kwargs):
    """
    File post-save processing:
     - conversion to XML of non-XML files
     - create/update notification on envelope's channel
    """
    channel_layer = get_channel_layer()
    payload = {'file_id': instance.pk}

    if created:
        async_to_sync(channel_layer.group_send)(
            instance.envelope.channel,
            {'type': f'envelope.added_{instance.channel_qualifier}', 'data': payload},
        )
    else:
        async_to_sync(channel_layer.group_send)(
            instance.envelope.channel,
            {'type': f'envelope.changed_{instance.channel_qualifier}', 'data': payload},
        )

    if instance.tracker.has_changed('file') and instance.extension != 'xml':
        instance.convert_to_xml()


class DataFileQuerySet(BaseEnvelopeFileQuerySet):

    def get_or_create(self, **kwargs):
        kwargs = self.process_kwargs(kwargs, 'data_files_path')
        return super().get_or_create(**kwargs)


class DataFile(BaseEnvelopeFile):

    CONVERSION_STATUS = Choices(
        (-1, 'error', _('error')),
        (0, 'na', _('na')),
        (1, 'running', _('running')),
        (2, 'finished', _('finished')),
    )

    channel_qualifier = 'data_file'

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

    objects = DataFileQuerySet.as_manager()
    tracker = FieldTracker()  # Trackers don't work when set on the abstract model

    class Meta(BaseEnvelopeFile.Meta):
        db_table = 'core_data_file'

    def get_upload_path(self, file_name):
        return os.path.join(self.envelope.data_files_path, file_name)

    def get_download_url(self):
        return reverse(
            'api:envelope-data-file-download',
            kwargs={'envelope_pk': self.envelope_id, 'pk': self.pk},
        )

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
        return QAJobResult.objects.filter(job__in=self.qa_jobs.all()).all()

    def delete_qa_feedback(self, force=False):
        """
        Deletes the file's `QAJob`s and corresponding `QAJobResult`s.

        Args:
            force(bool): Unless this is `True`, an exception is raised
             (and nothing is deleted) when there are unfinished jobs.

        """
        if not force and self.qa_jobs.filter(completed=False).exists():
            raise RuntimeError('Cannot delete incomplete QAJobs')

        self.qa_results.delete()

    def convert_to_xml(self):
        if self.extension == 'xml':
            raise RuntimeError('Cannot convert - file is already XML!')

        if self.original_file is not None:
            raise RuntimeError('Cannot convert an already converted file')

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


post_save.connect(after_file_save, sender=DataFile)


class SupportFileQuerySet(BaseEnvelopeFileQuerySet):

    def get_or_create(self, **kwargs):
        kwargs = self.process_kwargs(kwargs, 'support_files_path')
        return super().get_or_create(**kwargs)


class SupportFile(BaseEnvelopeFile):

    channel_qualifier = 'support_file'

    objects = SupportFileQuerySet.as_manager()
    tracker = FieldTracker()  # Trackers don't work when set on the abstract model

    class Meta(BaseEnvelopeFile.Meta):
        db_table = 'core_support_file'

    def get_upload_path(self, file_name):
        return os.path.join(self.envelope.support_files_path, file_name)

    def get_download_url(self):
        return reverse(
            'api:envelope-support-file-download',
            kwargs={'envelope_pk': self.envelope_id, 'pk': self.pk},
        )


post_save.connect(after_file_save, sender=SupportFile)


class Link(models.Model):
    envelope = models.ForeignKey(
        Envelope, on_delete=models.CASCADE, related_name='links'
    )
    link = models.URLField(max_length=500)
    text = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        db_table = 'core_link'
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
