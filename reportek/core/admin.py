from django.contrib import admin

from .models import (
    Country,
    Client,
    Issue,
    Instrument,
    Obligation,
)

from .models.reports import *

from .models.workflows import (
    WorkFlow,
    WFState,
    WFInitialState,
    WFTransition,
    WFTransitionSource
)

# Register your models here.

# ROD
admin.site.register(Country)
admin.site.register(Client)
admin.site.register(Issue)
admin.site.register(Instrument)
admin.site.register(Obligation)

# Workflows


class WFStateInline(admin.TabularInline):
    model = WFState


class WFInitialStateInline(admin.TabularInline):
    model = WFInitialState


@admin.register(WorkFlow)
class WorkFlowAdmin(admin.ModelAdmin):
    inlines = [
        WFStateInline,
        WFInitialStateInline,
    ]


class WFTransitionSourceInline(admin.TabularInline):
    model = WFTransitionSource


@admin.register(WFTransition)
class WFTransitionAdmin(admin.ModelAdmin):
    inlines = [
        WFTransitionSourceInline,
    ]


# Reports
# TODO: Register only the BaseReport without 'Untyped BaseReport cannot be saved' error

@admin.register(ReportLog)
class ReportLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'content_object', 'from_state', 'to_state']


admin.site.register(ReportSimple)
admin.site.register(ReportWithQA)
