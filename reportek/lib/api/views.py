from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.serializers import ValidationError
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin


class ValidatingCreateModelMixin(CreateModelMixin):
    """
    A DRF generic view mixin that handles Django's ValidationErrors
    on model creation.
    Should be used together with reportek.lib.db.models.ValidatingModel.
    """
    def perform_create(self, serializer):
        try:
            super().perform_create(serializer)
        except DjangoValidationError as err:
            raise ValidationError(err.message_dict)


class ValidatingUpdateModelMixin(UpdateModelMixin):
    """
    A DRF generic view mixin that handles Django's ValidationErrors
    on model update.
    Should be used together with reportek.lib.db.models.ValidatingModel.
    """
    def perform_update(self, serializer):
        try:
            super().perform_create(serializer)
        except DjangoValidationError as err:
            raise ValidationError(err.message_dict)
