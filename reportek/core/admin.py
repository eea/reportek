from django.contrib import admin

from .models import (
    Country,
    Client,
    Issue,
    Instrument,
    Obligation,
)

from .models.reports import (
    ReportOne,
)

from .models.workflows import (
    WorkFlow,
    WFState,
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
admin.site.register(WorkFlow)
admin.site.register(WFState)
admin.site.register(WFTransition)
admin.site.register(WFTransitionSource)

# Reports
admin.site.register(ReportOne)

