import os.path
from django.db import models
from django.contrib.postgres import fields as pgfields
from django.urls import reverse
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

    class Meta:
        unique_together = (
            ('obligation_group', 'country', 'reporting_period'),
        )

    def save(self, *args, **kwargs):
        # Force workflow to obligation group's one
        if not self.workflow or self.workflow != self.obligation_group.workflow:
            self.workflow = self.obligation_group.workflow

        super().save(*args, **kwargs)


class EnvelopeFile(models.Model):
    def get_envelope_directory(self, filename):
        return os.path.join(
            ENVELOPE_ROOT_DIR,
            self.envelope.slug,
            os.path.basename(filename)
        )

    envelope = models.ForeignKey(Envelope, related_name='files')
    file = protected.fields.ProtectedFileField(upload_to=get_envelope_directory)

    def get_file_url(self):
        return reverse('core:envelope-file', kwargs={
            'pk': self.envelope.pk,
            'filename': self.basename,
        })

    @property
    def basename(self):
        return os.path.basename(self.file.name)
