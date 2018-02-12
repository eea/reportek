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
from reportek.lib.db.models import ValidatingModel

from .workflows import (
    BaseWorkflow,
)

from .rod import (
    Reporter,
    ReporterSubdivision,
    Obligation,
    ObligationSpec,
    ObligationSpecReporter,
    ReportingCycle,
)

from .qa import QAJob, QAJobResult

from reportek.core.utils import get_xsd_uri

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
    'UploadToken'
]


class EnvelopeQuerySet(models.QuerySet):
    def open(self):
        return self.filter(finalized=False)

    def closed(self):
        return self.filter(finalized=True)


class EnvelopeManager(models.Manager.from_queryset(EnvelopeQuerySet)):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'reporter',
            'obligation_spec',
            'reporting_cycle',
            'workflow'
        )


class Envelope(ValidatingModel):
    name = models.CharField(max_length=256)

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

    class Meta:
        unique_together = (
            # this unique constraint is only true for non-continuous reporting,
            # so it's handled during validation
            # ('reporter', 'reporting_cycle', 'reporter_subdivision')
        )

    def __str__(self):
        return self.name

    def handle_auto_qa_results(self):
        return self.workflow.handle_auto_qa_results()

    def _check_envelope_uniqueness(self):
        unique_check = ('reporter', 'reporting_cycle', 'reporter_subdivision')

        if self.reporting_cycle.is_continuous:
            # TODO: there should be some sort of uniqueness here as well,
            # based on some envelope metadata (e.g. the reporting period...)
            return

        # this part adapted from Model._perform_unique_checks
        lookup_kwargs = {}
        for field_name in unique_check:
            f = self._meta.get_field(field_name)
            lookup_value = getattr(self, f.attname)
            lookup_kwargs[str(field_name)] = lookup_value

        model_class = self.__class__
        qs = model_class._default_manager.filter(**lookup_kwargs)

        # Exclude the current object from the query if we are updating
        model_class_pk = self._get_pk_val(model_class._meta)
        if not self._state.adding and model_class_pk is not None:
            qs = qs.exclude(pk=model_class_pk)

        if qs.exists():
            raise ValidationError(
                self.unique_error_message(model_class, unique_check)
            )

    def _check_reporter_subdivision(self):
        # override the exception locally, because lazy
        class _ValidationError(ValidationError):
            def __init__(self, msg, *args, **kwargs):
                super().__init__({'reporter_subdivision': msg})

        if self.reporter_subdivision is not None \
           and self.reporter != self.reporter_subdivision.reporter:
            raise _ValidationError(
                "Envelope's reporter subdivision does not match reporter."
            )

        # does the obligation require a subdivision?
        mapping = ObligationSpecReporter.objects.get(
            reporter=self.reporter,
            spec=self.obligation_spec,
        )

        category_id = mapping.subdivision_category_id
        subdivision = self.reporter_subdivision

        if category_id is None:
            if subdivision is not None:
                raise _ValidationError(
                    'This obligation does not accept a reporter subdivision.'
                )
        else:
            subdivision = self.reporter_subdivision
            if subdivision is None:
                raise _ValidationError(
                    'This obligation requires a reporter subdivision.'
                )
            if category_id != subdivision.category_id:
                raise _ValidationError(
                    'Invalid reporter subdivision for obligation.'
                )
            # that's all. duplicate subdivisions are checked under
            # _check_envelope_uniqueness()

    def clean(self):
        errors = {}

        # try to keep things modular a bit.
        # any method called here should raise ValidationError when needed
        for method in (
                # (don't forget about super)
                super().clean,
                self._check_envelope_uniqueness,
                self._check_reporter_subdivision,
        ):
            try:
                method()
            except ValidationError as e:
                errors = e.update_error_dict(errors)

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # don't allow any operations on a final envelope
        if self.tracker.changed() and self.tracker.previous('finalized'):
            raise RuntimeError("Envelope is final.")

        # On first save:
        if not self.pk or kwargs.get('force_insert', False):
            # creation expects only the reporting cycle (normally)
            if (self.obligation_spec_id is None
                and self.reporting_cycle_id is not None
            ):
                self.obligation_spec = self.reporting_cycle.obligation_spec

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

        # handled here as a RuntimeError (instead of ValidationError),
        # because the spec should never be set directly.
        if self.reporting_cycle is not None and \
           self.obligation_spec != self.reporting_cycle.obligation_spec:
            raise RuntimeError("Envelope's obligation_spec doesn't match "
                               "its reporting_cycle.")

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
        info(f'Deleting envelope file: {env_file}')
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


class EnvelopeFile(models.Model):

    class Meta:
        db_table = 'core_envelope_file'
        unique_together = ('envelope', 'name')

    def get_envelope_directory(self, filename):
        return os.path.join(
            self.envelope.get_storage_directory(),
            os.path.basename(filename)
        )

    envelope = models.ForeignKey(Envelope, related_name='files')
    file = protected.fields.ProtectedFileField(upload_to=get_envelope_directory,
                                               max_length=512)
    # initially derived from the filename, a change triggers rename
    name = models.CharField(max_length=256, validators=[validate_filename])

    xml_schema = models.CharField(max_length=200, blank=True, null=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # keep track of the name to handle renames
        self._prev_name = (None if self.pk is None
                           else self.name)

    def __repr__(self):
        return '<%s: %s/%s>' % (self.__class__.__name__,
                                self.envelope.pk,
                                self.name)

    @property
    def qa_results(self):
        try:
            return QAJobResult.objects.filter(job__in=self.qa_jobs.all()).all()
        except QAJobResult.DoesNotExist:
            return None

    def save(self, *args, **kwargs):
        # don't allow any operations on a final envelope
        if self.envelope.finalized:
            raise RuntimeError("Envelope is final.")

        renamed = False
        if self.pk is None:
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

    def get_file_url(self):
        return reverse('core:envelope-file', kwargs={
            'pk': self.envelope_id,
            'filename': self.name,
        })

    def get_api_download_url(self):
        return reverse('api:envelope-file-download', kwargs={
            'envelope_pk': self.envelope_id,
            'pk': self.pk,
        })

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

    @staticmethod
    def has_valid_extension(filename, include_archives=False):
        """
        Checks a file's extension against allowed extensions.
        If `include_archives` is `True`, extensions in
        `ALLOWED_UPLOADS_ARCHIVE_EXTENSIONS` are permitted.
        """
        allowed_extensions = settings.ALLOWED_UPLOADS_EXTENSIONS
        if include_archives:
            allowed_extensions += settings.ALLOWED_UPLOADS_ARCHIVE_EXTENSIONS
        return filename.split('.')[-1].lower() in allowed_extensions

    def extract_xml_schema(self):
        return get_xsd_uri(self.file.path)


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
