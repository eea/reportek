import os
import logging
from datetime import date
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db import models, transaction
from django.contrib.postgres import fields as pgfields
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _
from edw.djutils import protected
from model_utils import FieldTracker


from . import (
    Country,
    BaseWorkflow,
)

from reportek.core.models.workflows import WORKFLOW_CLASSES

log = logging.getLogger('reportek.workflows')
info = log.info
debug = log.debug
warn = log.warning
error = log.error


ENVELOPE_ROOT_DIR = "envelopes"

UPLOAD_TOKEN_LENGTH = 64
UPLOAD_TOKEN_DURATION = 60 * 60  # 60 minutes


class _BrowsableModel(models.Model):
    """
    Child classes must have a `name` field.
    """
    slug = models.SlugField(unique=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class ObligationGroupQuerySet(models.QuerySet):
    def pending(self):
        return self.filter(
            workflow_class__isnull=False,
            next_reporting_start__isnull=False,
            reporting_duration_months__isnull=False,
            next_reporting_start__lte=date.today(),
        )

    def open(self):
        return self.filter(
            workflow_class__isnull=False,
            reporting_period_set__open=True,
        )


class ObligationGroup(_BrowsableModel):
    name = models.CharField(max_length=256, unique=True)

    # the workflow is nullable to allow creation of the group
    # while its workflow doesn't exist, or by someone unprivileged
    workflow_class = models.CharField(
        max_length=256, null=True, blank=True,
        choices=WORKFLOW_CLASSES
    )

    next_reporting_start = models.DateField(blank=True, null=True)
    reporting_duration_months = models.PositiveSmallIntegerField(blank=True, null=True)

    objects = ObligationGroupQuerySet.as_manager()

    @property
    def open(self):
        return self.reporting_period_set.current().exists()

    def start_reporting_period(self):
        assert self.open is False
        assert (self.next_reporting_start is not None
                and date.today() >= self.next_reporting_start)
        assert self.reporting_duration_months is not None

        start, end = (
            self.next_reporting_start,
            self.next_reporting_start + relativedelta(
                months=self.reporting_duration_months
            )
        )

        with transaction.atomic():
            self.reporting_period_set.create(
                period=(start, end)
            )
            self.next_reporting_start = end
            self.save()

    def close_reporting_period(self):
        # TODO: this should be performed automatically when all parties
        # have submitted their reports(?)
        period = self.reporting_period_set.current().get()
        period.close()


class ReportingPeriodQuerySet(models.QuerySet):
    def current(self):
        return self.filter(open=True)


class ReportingPeriod(models.Model):
    obligation_group = models.ForeignKey(ObligationGroup,
                                         related_name="reporting_period_set")
    period = pgfields.DateRangeField()
    open = models.BooleanField(default=True)

    objects = ReportingPeriodQuerySet.as_manager()

    class Meta:
        unique_together = (
            ('obligation_group', 'period'),
        )

    def __str__(self):
        return '%s: %s - %s' % (
            self.obligation_group, self.period.lower, self.period.upper
        )

    def save(self, *args, **kwargs):
        if not self.pk or kwargs.get('force_insert', False):
            if self.obligation_group.open:
                # TODO: make this a ValidationError
                raise RuntimeError("Reporting period already open for %s."
                                   % self.obligation_group)

        # TODO: one can still re-open a previously closed period
        # and make a mess of things. fix it.
        super().save(*args, **kwargs)

    def close(self):
        assert self.open is True
        self.open = False
        self.save()


class Collection(_BrowsableModel):
    """
    This is just a nice way to arbitrarily group things.
    It has no other purpose but to improve browsability.
    """
    name = models.CharField(max_length=256, unique=True)

    countries = models.ManyToManyField(Country)
    obligation_groups = models.ManyToManyField(ObligationGroup)


class EnvelopeQuerySet(models.QuerySet):
    pass


class EnvelopeManager(models.Manager.from_queryset(EnvelopeQuerySet)):
    def get_queryset(self):
        # we want to always fetch the reporting period along
        return super().get_queryset().select_related('reporting_period')


class Envelope(_BrowsableModel):
    name = models.CharField(max_length=256)
    obligation_group = models.ForeignKey(ObligationGroup)
    country = models.ForeignKey(Country)
    reporting_period = models.ForeignKey(ReportingPeriod)
    workflow = models.OneToOneField(BaseWorkflow,
                                    on_delete=models.CASCADE,
                                    related_name='envelope',
                                    null=True, blank=True)
    # TODO: this must never change, it's used below. must guard against it.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    finalized = models.BooleanField(default=False)

    objects = EnvelopeManager()
    tracker = FieldTracker()

    class Meta:
        unique_together = (
            ('obligation_group', 'country', 'reporting_period'),
        )

    def save(self, *args, **kwargs):
        # don't allow any operations on a final envelope
        if self.tracker.changed() and self.tracker.previous('finalized'):
            raise RuntimeError("Envelope is final.")

        # On first save:
        if not self.pk or kwargs.get('force_insert', False):
            # - set the current reporting period
            self.reporting_period = ReportingPeriod.objects.current().get(
                obligation_group=self.obligation_group
            )

            # - import the workflow class set on the envelope's obligation group
            # TODO: move this logic under ObligationGroup
            wf_path_components = self.obligation_group.workflow_class.split('.')
            mod_name = '.'.join(wf_path_components[:-1])
            class_name = wf_path_components[-1]
            mod = __import__(mod_name, fromlist=[class_name])
            # Instantiate a new workflow and set it on the envelope
            wf_class = getattr(mod, class_name)
            workflow = wf_class(name=f'Envelope "{self.name}"\'s workflow')
            workflow.save()
            self.workflow = workflow

        super().save(*args, **kwargs)

    def get_storage_directory(self):
        # generate a multi-level, stable path. say...
        # reporting year / country / obligation group / envelope id
        # TODO: switch to slugs? (and handle renames?)

        year = str(
            self.created_at.year
            if self.reporting_period.period.upper_inf
            else self.reporting_period.period.upper.year
        )
        country = self.country.slug
        ogroup = str(self.obligation_group_id)
        envelope = str(self.id)

        return os.path.join(ENVELOPE_ROOT_DIR,
                            year, country, ogroup, envelope)

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
    # TODO: rename this (and reset migrations)
    #def get_upload_path(self, filename):
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

    class Meta:
        unique_together = ('envelope', 'name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # keep track of the name to handle renames
        self._prev_name = (None if self.pk is None
                           else self.name)

    def __repr__(self):
        return '<%s: %s/%s>' % (self.__class__.__name__,
                                self.envelope.pk,
                                self.name)

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

        print(f'saving file name: {self.file.name}')
        # save first to catch data integrity errors.
        # TODO: wrap this in a transaction with below, who knows
        # how that might fail...
        super().save(*args, **kwargs)

        # and rename on disk
        if renamed:
            print('renamed: {old_path} to {new_path}')
            os.rename(old_path, new_path)

    def get_file_url(self):
        return reverse('core:envelope-file', kwargs={
            'pk': self.envelope_id,
            'filename': self.name,
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
        ordering = ('-created_at',)

    def __str__(self):
        return f'Upload token for user "{self.user}" ' \
               f'on envelope "{self.envelope}"'

    def has_expired(self):
        return self.valid_until < (
            timezone.now() + timezone.timedelta(seconds=self.GRACE_SECONDS))
