from datetime import date
from django.db import models
from django.contrib.postgres.fields import ArrayField


class RODModel(models.Model):
    URL_PATTERN = None

    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    @property
    def url(self):
        return self.URL_PATTERN.format(id=self.id)

    class Meta:
        abstract = True


class Client(RODModel):
    URL_PATTERN = 'http://rod.eionet.europa.eu/clients/{id}'

    name = models.CharField(max_length=256)
    abbr = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.name + (f' ({self.abbr})' if self.abbr else '')


class Reporter(RODModel):
    """
    The reporting entity (usually countries in CDR and companies in BDR,
    but can be other types of organisations as well).
    """
    URL_PATTERN = 'http://rod.eionet.europa.eu/reporters/{id}'

    name = models.CharField(max_length=256)
    abbr = models.CharField(max_length=32, unique=True)

    @property
    def slug(self):
        return self.abbr.lower()

    def __str__(self):
        return f'{self.name} [{self.abbr}]'


class ReporterSubdivisionCategory(RODModel):
    """
    Sometimes reporting for a certain country, for a certain obligation,
    must be split across subdivisions (usually territorial).
    This is the parent category for each such subdivisions.
    """
    URL_PATTERN = 'http://rod.eionet.europa.eu/reporter-subdivision-categories/{id}'

    reporter = models.ForeignKey(Reporter)
    name = models.CharField(max_length=128)


class ReporterSubdivision(RODModel):
    """
    Reporting subdivions.
    """
    URL_PATTERN = 'http://rod.eionet.europa.eu/reporter-subdivisions/{id}'

    category = models.ForeignKey(ReporterSubdivisionCategory)
    name = models.CharField(max_length=128)


class Instrument(RODModel):
    """
    Legislative instrument. It's what creates obligations.
    """
    URL_PATTERN = 'http://rod.eionet.europa.eu/instruments/{id}'

    title = models.CharField(max_length=256)

    def __str__(self):
        return self.title


class Obligation(RODModel):
    """
    The reporting obligation.
    """
    URL_PATTERN = 'http://rod.eionet.europa.eu/obligations/{id}'

    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    # Nullable because there is a single obligation in ROD (746) that
    # has '0' as FK_SOURCE_ID
    instrument = models.ForeignKey(Instrument, blank=True, null=True)
    terminated = models.BooleanField(default=False)

    # this part specifies the recurrence rule.
    # the start & end dates for the entire lifetime of the obligation:
    active_since = models.DateTimeField()
    active_until = models.DateTimeField(null=True)
    # only recurrent obligations have duration and frequency,
    # both expressed in months.
    reporting_duration = models.SmallIntegerField(null=True)
    reporting_frequency = models.SmallIntegerField(null=True)

    @property
    def is_continuous(self):
        return self.reporting_duration is None

    @property
    def spec(self):
        """the current spec"""
        return self.specs.get(current=True)

    @property
    def clients(self):
        return self.spec.clients

    @property
    def reporters(self):
        return self.spec.reporters

    @property
    def reporter_subdivision_categories(self):
        """
        this is a computed property, to help avoid exposing the
        m2m table below in the API.
        """
        pass


class ObligationSpec(RODModel):
    """
    The obligation specification, aka Dataset Definition.
    Varies from one reporting cycle to another.
    """
    URL_PATTERN = 'http://rod.eionet.europa.eu/obligation-specs/{id}'

    obligation = models.ForeignKey(Obligation, related_name='specs')
    # increment version number for each spec change. TODO: do we want semver?
    version = models.PositiveSmallIntegerField(default=1)
    # implementation logic must make sure there's only one spec current per obligation.
    # each new reporting cycle will default to the obligation's current spec.
    is_current = models.BooleanField(default=False)
    # allow working on the new spec before making it official.
    draft = models.BooleanField(default=True)

    clients = models.ManyToManyField(Client)
    reporters = models.ManyToManyField(Reporter, through='ObligationSpecReporterMapping')
    schema = ArrayField(
        models.URLField(max_length=1024)
    )


class ObligationSpecReporterMapping(models.Model):
    spec = models.ForeignKey(ObligationSpec)
    reporter = models.ForeignKey(Reporter)
    # this is required only when reporting for the current entity
    # must be split across subdivisions
    subdivision_category = models.ForeignKey(ReporterSubdivisionCategory,
                                             blank=True, null=True)


class ReportingCycle(RODModel):
    """
    Reporting cycles, per obligation. Each report is tied to a specific cycle.
    """
    URL_PATTERN = 'http://rod.eionet.europa.eu/reporting-cycles/{id}'

    obligation = models.ForeignKey(Obligation)
    obligation_spec = models.ForeignKey(ObligationSpec)

    # this is always required, and can be in the future
    reporting_start_date = models.DateField()

    # - for standard (recurring) obligations, this is equivalent to the deadline date.
    # - for continuous-reporting obligations, this is null. in this case the period is
    #   initially open-ended, but this field gets a value when the period is closed.
    reporting_end_date = models.DateField(blank=True, null=True)

    # - for standard obligations, the reporting period should normally close
    #   when the deadline is hit, but in practice some reporters are lagging behind,
    #   or sometimes a period has to be reopen.
    # - for continuous-reporting, closing will happen when there is a need to start
    #   a new period (e.g. because of a schema change), or when the obligation terminates.
    is_open = models.BooleanField(default=True)

    @property
    def is_soft_closed(self):
        return (self.is_open and
                self.reporting_end_date is not None and
                self.reporting_end_date < date.today())
