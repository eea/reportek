from django.db import models
from django.contrib.auth.models import (
    UserManager as DefaultUserManager,
    AbstractUser,
)
from typedmodels.models import TypedModel

from reportek.core.models import Reporter


class UserManager(DefaultUserManager):
    def get_queryset(self):
        # select the reporter object by default.
        return super().get_queryset().select_related('reporter')


class User(AbstractUser, TypedModel):
    """
    Roles are embedded within the user model.
    To create a new role, simply extend this class.
    """

    objects = UserManager()

    def save(self, *args, **kwargs):
        # make sure that users created by default tools get a type
        if self.pk is None and not self.type:
            # typedmodels is a bit fidgety
            self.type = self._typedmodels_type = PlatformUser._typedmodels_type
        return super().save(*args, **kwargs)

    def is_reporter(self):
        return self.type == ReporterUser._typedmodels_type

    def is_manager(self):
        return self.type == ManagerUser._typedmodels_type

    @property
    def role(self):
        return {
            None: None,
            PlatformUser._typedmodels_type: "internal",
            ReporterUser._typedmodels_type: "reporter",
            ManagerUser._typedmodels_type: "manager",
        }[self.type]


class PlatformUser(User):
    """
    A user without a role. Created by default by management commands.
    """
    pass


class ReporterUser(User):
    """
    A Reportek reporter.
    """
    reporter = models.ForeignKey(Reporter, related_name="users")


class ManagerUser(User):
    """
    A Reportek manager.
    """
    pass
