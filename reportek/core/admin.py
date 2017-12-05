"""
from django.contrib import admin
from django_object_actions import DjangoObjectActions

from .models import (
    Country,
    Client,
    Issue,
    Instrument,
    Obligation,
)

from .models.workflows import (
    DemoAutoQAWorkflow,
    TransitionEvent,
)

from .models.reporting import (
    ObligationGroup,
    ReportingPeriod,
    Envelope,
)

# Register your models here.

# ROD
admin.site.register(Country)
admin.site.register(Client)
admin.site.register(Issue)
admin.site.register(Instrument)
admin.site.register(Obligation)

# Workflows


@admin.register(TransitionEvent)
class TransitionEventAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'content_object', 'transition', 'from_state', 'to_state']


admin.site.register(DemoAutoQAWorkflow)


# Reporting
@admin.register(ObligationGroup)
class ObligationGroupAdmin(DjangoObjectActions, admin.ModelAdmin):
    def start_reporting_period(self, request, obj):
        obj.start_reporting_period()
    start_reporting_period.label = "Start Reporting Period"

    def close_reporting_period(self, request, obj):
        obj.close_reporting_period()
    close_reporting_period.label = "Close Reporting Period"

    change_actions = ('start_reporting_period', 'close_reporting_period')


@admin.register(ReportingPeriod)
class ReportingPeriodAdmin(admin.ModelAdmin):
    def xperiod(self, obj):
        return '%s - %s' % (obj.period.lower, obj.period.upper)
    xperiod.short_description = "Period"

    list_display = ('obligation_group', 'xperiod', 'open')

admin.site.register(Envelope)
"""
