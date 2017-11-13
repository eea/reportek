from rest_framework import viewsets

from .models import (
    Envelope, EnvelopeFile,
)
from .serializers import (
    EnvelopeSerializer, EnvelopeFileSerializer,
)
from . import permissions


class EnvelopeViewSet(viewsets.ModelViewSet):
    queryset = Envelope.objects.all()
    serializer_class = EnvelopeSerializer
    permission_classes = (permissions.IsAuthenticated, )


class EnvelopeFileViewSet(viewsets.ModelViewSet):
    queryset = EnvelopeFile.objects.all()
    serializer_class = EnvelopeFileSerializer
    permission_classes = (permissions.IsAuthenticated, )
