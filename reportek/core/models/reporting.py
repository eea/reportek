import os
from django.db import models
from django.contrib.postgres import fields as pgfields
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from edw.djutils import protected

from . import (
    Country,
    BaseWorkflow,
)

ENVELOPE_ROOT_DIR = "envelopes"


class _BrowsableModel(models.Model):
    """
    Child classes must have a `name` field.
    """
    slug = models.SlugField(unique=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class ObligationGroup(_BrowsableModel):
    name = models.CharField(max_length=256, unique=True)

    # the workflow is nullable to allow creation of the group
    # while its workflow doesn't exist, or by someone unprivileged
    workflow = models.ForeignKey(BaseWorkflow, null=True, blank=True)


class Collection(_BrowsableModel):
    """
    This is just a nice way to arbitrarily group things.
    It has no other purpose but to improve browsability.
    """
    name = models.CharField(max_length=256, unique=True)

    countries = models.ManyToManyField(Country)
    obligation_groups = models.ManyToManyField(ObligationGroup)


class Envelope(_BrowsableModel):
    name = models.CharField(max_length=256)
    obligation_group = models.ForeignKey(ObligationGroup)
    country = models.ForeignKey(Country)
    # TODO: the reporting period needs to be derived from the obligation
    reporting_period = pgfields.DateRangeField()
    workflow = models.OneToOneField(BaseWorkflow,
                                    on_delete=models.CASCADE,
                                    related_name='envelope',
                                    null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (
            ('obligation_group', 'country', 'reporting_period'),
        )

    def save(self, *args, **kwargs):
        # Force workflow to obligation group's one
        if not self.workflow or self.workflow != self.obligation_group.workflow:
            self.workflow = self.obligation_group.workflow

        super().save(*args, **kwargs)


# TODO: move me somewhere nice (and improve me)
def validate_filename(value):
    if os.path.basename(os.path.join('test', value)) != value:
        raise ValidationError(
            _("'%(value)s' is not a valid file name"),
            params={'value': value},
        )


class EnvelopeFile(models.Model):
    def get_envelope_directory(self, filename):
        return os.path.join(
            ENVELOPE_ROOT_DIR,
            self.envelope.slug,
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

        # save first to catch data integrity errors.
        # TODO: wrap this in a transaction with below, who knows
        # how that might fail...
        super().save(*args, **kwargs)

        # and rename on disk
        if renamed:
            os.rename(old_path, new_path)

    def get_file_url(self):
        return reverse('core:envelope-file', kwargs={
            'pk': self.envelope.pk,
            'filename': self.name,
        })
