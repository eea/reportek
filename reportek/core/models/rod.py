from django.db import models


class Client(models.Model):
    name = models.CharField(max_length=200)
    acronym = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.name + (f' ({self.acronym})' if self.acronym else '')


class Country(models.Model):
    # root URL http://rod.eionet.europa.eu/spatial/
    class Meta:
        verbose_name_plural = 'countries'
    iso = models.CharField(max_length=2, unique=True)
    name = models.CharField(max_length=60)

    def __str__(self):
        return f'{self.name} [{self.iso}]'

    @property
    def slug(self):
        return self.iso.lower()


class Issue(models.Model):
    """Environmental issues"""
    name = models.CharField(max_length=60)

    def __str__(self):
        return self.name


class InstrumentQuerySet(models.QuerySet):
    def for_country(self, country):
        obligations = Obligation.objects.for_country(country)
        return self.filter(
            obligation__in=obligations.values_list('pk', flat=True)
        ).distinct()


class Instrument(models.Model):
    """Legislative instruments"""
    title = models.CharField(max_length=256)

    objects = InstrumentQuerySet.as_manager()

    def __str__(self):
        return self.title

    @property
    def slug(self):
        return self.pk


class ObligationQuerySet(models.QuerySet):
    def for_country(self, country):
        if isinstance(country, models.Model):
            country = country.pk
        return self.filter(delivery_countries__pk=country)


class Obligation(models.Model):
    """Reporting obligations"""
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    # TODO: Clarify if nullable (no empties present in ROD dump)
    last_update = models.DateField()
    next_deadline = models.DateField(blank=True, null=True)
    next_deadline2 = models.DateField(blank=True, null=True)
    report_freq_months = models.IntegerField(blank=True, null=True)
    report_freq = models.CharField(max_length=30, blank=True, null=True)
    continuous_reporting = models.BooleanField(default=False)
    client = models.ForeignKey(Client)
    # Nullable because there is a single obligation in ROD (746) that
    # has '0' as FK_SOURCE_ID
    instrument = models.ForeignKey(Instrument, blank=True, null=True)
    delivery_countries = models.ManyToManyField(Country)
    group = models.ForeignKey('core.ObligationGroup', null=True, blank=True)

    objects = ObligationQuerySet.as_manager()

    URL_PATTERN = 'http://rod.eionet.europa.eu/obligations/{id}'

    def __str__(self):
        return self.title

    @property
    def slug(self):
        return self.pk
