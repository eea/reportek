from django.contrib import admin

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
admin.site.register(ObligationGroup)
admin.site.register(Envelope)
