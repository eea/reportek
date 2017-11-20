from rest_framework.permissions import BasePermission, IsAuthenticated


class IsAnonymous(BasePermission):
    def has_permission(self, request, view):
        return not request.user.is_authenticated()


class BasePermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        # don't return True by default
        return self.has_permission(request, view)


class IsAuthenticated(BasePermission, IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_active


class IsAuthenticatedOrEnvelopeIsPublic(IsAuthenticated):
    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return obj.finalized or super().has_permission(request, view)
