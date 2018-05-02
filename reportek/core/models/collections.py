from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from mptt.models import MPTTModel, TreeForeignKey
from model_utils import FieldTracker

from .rod import Reporter, Obligation
from .reporting import Envelope


__all__ = ['Collection']


class Collection(MPTTModel):

    name = models.CharField(max_length=200)
    parent = TreeForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='children'
    )

    reporter = models.ForeignKey(Reporter, on_delete=models.CASCADE, null=True, blank=True)

    obligations = models.ManyToManyField(Obligation, related_name='collections', blank=True)

    coverage_start_year = models.IntegerField(null=True, blank=True)
    coverage_end_year = models.IntegerField(null=True, blank=True)
    coverage_interval = models.IntegerField(
        null=True, blank=True, choices=Envelope.COVERAGE_INTERVAL_CHOICE
    )
    coverage_note = models.CharField(max_length=256, null=True, blank=True)

    allows_envelopes = models.BooleanField(default=True)
    allows_collections = models.BooleanField(default=False)
    allows_referrals = models.BooleanField(default=False)

    deprecated = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    tracker = FieldTracker()

    def __str__(self):
        return self.name

    class MPTTMeta:
        order_insertion_by = ['name']

    @cached_property
    def ancestors(self):
        return self.get_ancestors(ascending=False).all()

    def clean(self):
        if self.reporter is not None:
            allowed_reporter = self._get_first_in_ancestors('reporter')
            if allowed_reporter is not None and allowed_reporter != self.reporter:
                raise ValidationError(
                    _('Cannot set a collection reporter different from ancestor\'s')
                )

        if not self.parent.allows_collections:
            raise ValidationError(
                _('Parent collection does not allow subcollections')
            )

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.deprecated and self.tracker.has_changed('deprecated'):
                for child in self.get_children():
                    child.deprecated = True
                    child.save()

            super().save(*args, **kwargs)

    def _get_first_in_ancestors(self, attr_name):
        """
        Walks up the collection's ancestors and retrieves the first populated attribute.
        """
        if attr_name in [f.name for f in self._meta.fields]:
            for ancestor in self.ancestors:
                a_attr = getattr(ancestor, attr_name)
                if a_attr is not None:
                    return a_attr
            return None
        elif attr_name in [f.name for f in self._meta.local_many_to_many]:
            for ancestor in self.ancestors:
                a_attr = getattr(ancestor, attr_name).all()
                if a_attr:
                    return a_attr
            return []

    def get_reporter(self):
        return self.reporter or self._get_first_in_ancestors('reporter')

    def get_obligations(self):
        return self.obligations.all() or self._get_first_in_ancestors('obligations')

    def get_coverage_start_year(self):
        return self.coverage_start_year or self._get_first_in_ancestors('coverage_start_year')

    def get_coverage_end_year(self):
        return self.coverage_end_year or self._get_first_in_ancestors('coverage_end_year')

    def get_coverage_interval(self):
        return self.coverage_interval or self._get_first_in_ancestors('coverage_interval')

    def get_coverage_note(self):
        return self.coverage_note or self._get_first_in_ancestors('coverage_note')
