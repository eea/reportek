from django.contrib import admin

from .models import (
    Country,
    Client,
)

# Register your models here.
admin.site.register(Country)
admin.site.register(Client)

