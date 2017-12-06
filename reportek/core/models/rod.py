import enum
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


class ENTITY_ROLES(enum.IntEnum):
    OBSERVER = 0
    CLIENT = 1
    REPORTER = 2


class Entity(RODModel):
    """
    Any entity involved in the reporting process, be it an organisation,
    country, company etc.
    They can assume different roles for different obligations
    (e.g. be a client for an obligation while being a reporter for another,
    or be an observing party or play another (yet unknown) role).
    """
    URL_PATTERN = 'http://rod.eionet.europa.eu/entities/{id}'

    name = models.CharField(max_length=256)
    abbr = models.CharField(max_length=32, unique=True)

    @property
    def slug(self):
        return self.abbr.lower()

    def __str__(self):
        return f'{self.name} [{self.abbr}]'


class EntitySubdivisionCategory(RODModel):
    """
    Sometimes reporting for a certain country, for a certain obligation,
    must be split across subdivisions (usually territorial).
    This is the parent category for each such subdivisions.
    """
    URL_PATTERN = 'http://rod.eionet.europa.eu/entity-subdivision-categories/{id}'

    entity = models.ForeignKey(Entity)
    name = models.CharField(max_length=128)


class EntitySubdivision(RODModel):
    """
    Reporting subdivions.
    """
    URL_PATTERN = 'http://rod.eionet.europa.eu/entity-subdivisions/{id}'

    category = models.ForeignKey(EntitySubdivisionCategory)
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

    entities = models.ManyToManyField(Entity, through='ObligationSpecEntityRoles')
    schema = ArrayField(
        models.URLField(max_length=1024)
    )

    @property
    def clients(self):
        return self.entities.filter(roles__role=ENTITY_ROLES.CLIENT)

    @property
    def reporters(self):
        return self.entities.filter(roles__role=ENTITY_ROLES.REPORTER)


class ObligationSpecEntityRoles(models.Model):
    spec = models.ForeignKey(ObligationSpec)
    entity = models.ForeignKey(Entity)
    role = models.PositiveSmallIntegerField(choices=((r.value, r.name.title())
                                                     for r in ENTITY_ROLES))
    # this is required only when reporting for the current entity
    # must be split across subdivisions
    subdivision_category = models.ForeignKey(EntitySubdivisionCategory,
                                             blank=True, null=True)

    class Meta:
        default_related_name = 'roles'


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
