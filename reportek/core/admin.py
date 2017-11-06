from django.contrib import admin

from .models import (
    Country,
    Client,
    Issue,
    Instrument,
    Obligation,
)

# Register your models here.
admin.site.register(Country)
admin.site.register(Client)
admin.site.register(Issue)
admin.site.register(Instrument)
admin.site.register(Obligation)
