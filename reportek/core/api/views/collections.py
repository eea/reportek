from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination

from ...models import Collection
from ...serializers import CollectionSerializer


__all__ = ['CollectionsViewSet']


class CollectionResultsSetPagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 100


class CollectionsViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Collection.objects.filter(deprecated=False)
    serializer_class = CollectionSerializer
    pagination_class = CollectionResultsSetPagination

    def get_queryset(self):
        """
        Collections can be filtered on the reporter.
        The results describe a partial tree, that includes the ancestors and
        descendants of instances with a concrete reporter.

        Note:
            View consumers must be aware that some of the ancestor's children
            may have a different reporter - only collections included
            in the filtered results should be considered when representing the
            tree.
        """
        queryset = Collection.objects.filter(deprecated=False)
        reporter = self.request.query_params.get('reporter', None)
        if reporter is None:
            return queryset

        colls_with_reporter = queryset.filter(reporter=reporter)
        ancestors = Collection.objects.none()
        for coll in colls_with_reporter:
            ancestors = ancestors | coll.get_ancestors()

        descendants = Collection.objects.none()
        for coll in colls_with_reporter:
            descendants = descendants | coll.get_descendants()

        return (colls_with_reporter | ancestors | descendants).distinct()
