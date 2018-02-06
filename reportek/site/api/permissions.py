from rest_framework.permissions import IsAuthenticated


class IsSiteUser(IsAuthenticated):
    def has_permission(self, request, view):
        return (
            super().has_permission(request, view)
            and request.user.is_active
        )


class IsReporter(IsSiteUser):
    def has_permission(self, request, view):
        return (
            super().has_permission(request, view)
            and request.user.is_reporter()
        )
