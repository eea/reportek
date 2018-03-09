
from rest_framework.pagination import LimitOffsetPagination


class DefaultPagination(LimitOffsetPagination):
    default_limit = 20
    max_limit = 100


class MappedPermissionsMixin:
    """
    Provides a `get_permissions` implementation that sources permissions
    from a `permission_classes_map` class attribute, e.g.:

    ```
        permission_classes_map = {
            'default': [permissions.MyModelPermissions],
            'list': [IsAuthenticatedOrReadOnly],
            'retrieve': [IsAuthenticatedOrReadOnly]
        }
    ```
    """

    def get_permissions(self):
        try:
            return [permission() for permission in self.permission_classes_map[self.action]]
        except KeyError:
            return [permission() for permission in self.permission_classes_map['default']]
