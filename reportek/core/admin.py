from django.contrib import admin

from .models import (
    Country,
    Client,
    Issue,
)

# Register your models here.
admin.site.register(Country)
admin.site.register(Client)
admin.site.register(Issue)

