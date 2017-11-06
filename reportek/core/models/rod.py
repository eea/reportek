from django.db import models


class Client(models.Model):
    name = models.CharField(max_length=200)
    acronym = models.CharField(max_length=20, blank=True)


class Country(models.Model):
    # root URL http://rod.eionet.europa.eu/spatial/
    class Meta:
        verbose_name_plural = 'countries'
    iso = models.CharField(max_length=2, unique=True)
    name = models.CharField(max_length=60)


class Issue(models.Model):
    """Environmental issues"""
    name = models.CharField(max_length=60)


class Instrument(models.Model):
    """Legislative instruments"""
    title = models.CharField(max_length=256)


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

    URL_PATTERN = 'http://rod.eionet.europa.eu/obligations/{id}'

