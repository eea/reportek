
from django.contrib import admin
from guardian.admin import GuardedModelAdmin
from django_object_actions import DjangoObjectActions

from .models import (
    Reporter,
    ReporterSubdivisionCategory,
    ReporterSubdivision,
    Client,
    Instrument,
    Obligation,
    ObligationSpec,
    ObligationSpecReporter,
    ReportingCycle,
    Envelope,
    DemoAutoQAWorkflow,
    TransitionEvent
)


# ROD


@admin.register(Reporter)
class ReporterAdmin(GuardedModelAdmin):
    search_fields = ('name', 'abbr')
    ordering = ('name',)


admin.site.register(ReporterSubdivision)
admin.site.register(ReporterSubdivisionCategory)


@admin.register(Client)
class ClientAdmin(GuardedModelAdmin):
    search_fields = ('name', 'abbr')
    ordering = ('name',)


admin.site.register(Instrument)


@admin.register(Obligation)
class ObligationAdmin(GuardedModelAdmin):
    list_display = ('title', 'instrument')
    search_fields = ('title', 'instrument__title')
    ordering = ('title',)


class ObligationSpecReporterAdmin(admin.TabularInline):
    model = ObligationSpec.reporters.through


@admin.register(ObligationSpec)
class ObligationSpecAdmin(admin.ModelAdmin):
    inlines = [ObligationSpecReporterAdmin, ]

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_current:
            return self.readonly_fields + ('is_current',)
        return self.readonly_fields


admin.site.register(ReportingCycle)


# Workflows
@admin.register(TransitionEvent)
class TransitionEventAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'content_object', 'transition', 'from_state', 'to_state']


admin.site.register(DemoAutoQAWorkflow)


# Reporting

admin.site.register(Envelope)

# @admin.register(ObligationGroup)
# class ObligationGroupAdmin(DjangoObjectActions, admin.ModelAdmin):
#     def start_reporting_period(self, request, obj):
#         obj.start_reporting_period()
#     start_reporting_period.label = "Start Reporting Period"
#
#     def close_reporting_period(self, request, obj):
#         obj.close_reporting_period()
#     close_reporting_period.label = "Close Reporting Period"
#
#     change_actions = ('start_reporting_period', 'close_reporting_period')
#
#
# @admin.register(ReportingPeriod)
# class ReportingPeriodAdmin(admin.ModelAdmin):
#     def xperiod(self, obj):
#         return '%s - %s' % (obj.period.lower, obj.period.upper)
#     xperiod.short_description = "Period"
#
#     list_display = ('obligation_group', 'xperiod', 'open')
#
#

