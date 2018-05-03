from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from guardian.admin import GuardedModelAdmin
from mptt.admin import MPTTModelAdmin
from django_object_actions import DjangoObjectActions

from .models import (
    Reporter,
    ReporterSubdivisionCategory,
    ReporterSubdivision,
    Client,
    Instrument,
    Obligation,
    ObligationSpec,
    Collection,
    ReportingCycle,
    Envelope,
    # DemoAutoQAWorkflow,
    TransitionEvent
)


user_model = get_user_model()


class ReportekUserAdmin(UserAdmin):

    fieldsets = UserAdmin.fieldsets + (
                    ('Effective permissions', {'fields': ('ldap_group_names', 'effective_group_names')}),
                )
    readonly_fields = UserAdmin.readonly_fields + ('ldap_group_names', 'effective_group_names')

    def ldap_group_names(self, instance):
        return ', '.join(sorted([g.name for g in instance.ldap_groups]))

    ldap_group_names.short_description = 'LDAP groups'

    def effective_group_names(self, instance):
        return ', '.join(sorted([g.name for g in instance.effective_groups]))

    effective_group_names.short_description = 'Effective groups'


admin.site.register(user_model, ReportekUserAdmin)


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


# admin.site.register(DemoAutoQAWorkflow)


# Reporting

admin.site.register(Envelope)

admin.site.register(Collection, MPTTModelAdmin)
