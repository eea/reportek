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
