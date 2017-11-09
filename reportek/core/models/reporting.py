import os.path
from django.db import models
from django.contrib.postgres import fields as pgfields

from . import (
    Country,
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
    workflow = models.CharField(max_length=256, null=True)


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

    class Meta:
        unique_together = (
            ('obligation_group', 'country', 'reporting_period'),
        )


class EnvelopeFile(models.Model):
    def get_envelope_directory(self, filename):
        return os.path.join(
            ENVELOPE_ROOT_DIR,
            self.envelope.slug,
            os.path.basename(filename)
        )

    envelope = models.ForeignKey(Envelope)
    file = models.FileField(upload_to=get_envelope_directory)
