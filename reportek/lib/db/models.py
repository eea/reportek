from django.db import models


class ValidatingModel(models.Model):
    """
    An abstract model that runs `self.full_clean()` before every save.
    """
    # to consolidate data validation / business logic under the model.
    # this is an adaptation of the solution under
    # https://github.com/encode/django-rest-framework/issues/2145#issuecomment-260080084

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__clean_fields_has_run = False
        self.__clean_has_run = False
        self.__validate_unique_has_run = False

    # the following methods exist in order to avoid multiple validations
    # (such as those caused by ModelForms, which run a custom full_clean).
    # (ideally the state variables would be reset after each modification,
    # but nobody runs a validation, then modifies the data, then saves ....
    # ... right?)
    def clean_fields(self, exclude=None):
        if not exclude:
            if self.__clean_fields_has_run:
                return
            self.__clean_fields_has_run = True
        super().clean_fields(exclude=exclude)


    def clean(self):
        if self.__clean_has_run:
            return
        self.__clean_has_run = True
        super().clean()


    def validate_unique(self, exclude=None):
        if not exclude:
            if self.__validate_unique_has_run:
                return
            self.__validate_unique_has_run = True
        super().validate_unique(exclude=exclude)
