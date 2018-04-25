from django.db import models


class ValidateOnSaveMixin:

    def save(self: models.Model, force_insert=False, force_update=False, **kwargs):
        if not (force_insert or force_update):
            self.full_clean()
        super().save(force_insert, force_update, **kwargs)
