from rest_framework import viewsets, status
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from .models import (
    Envelope,
    EnvelopeFile,
    BaseWorkflow,
)
from .serializers import (
    EnvelopeSerializer,
    EnvelopeFileSerializer,
    NestedEnvelopeWorkflowSerializer
)
from . import permissions


class EnvelopeViewSet(viewsets.ModelViewSet):
    queryset = Envelope.objects.all()
    serializer_class = EnvelopeSerializer
    permission_classes = (permissions.IsAuthenticated, )

    @detail_route(methods=['post'])
    def transition(self, request, pk):
        """
        Initiates a transition, expects `transition_name` in the POST data.
        """
        envelope = self.get_object()
        workflow = envelope.workflow
        transition_name = request.data.get('transition_name')

        try:
            transition = getattr(workflow.xwf, transition_name)
        except AttributeError:
            return Response(
                {
                    'transition': transition_name,
                    'current_state': workflow.current_state,
                    'error': 'Invalid transition name'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if not transition.is_available():
            return Response(
                {
                    'transition': transition_name,
                    'current_state': workflow.current_state,
                    'error': 'Transition not allowed from current state'
                },
                status=status.HTTP_406_NOT_ACCEPTABLE
            )

        try:
            transition()
        except Exception as err:
            return Response(
                {
                    'transition': transition_name,
                    'current_state': workflow.current_state,
                    'error': err
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {
                'transition': transition_name,
                'current_state': workflow.current_state
            }
        )


class EnvelopeFileViewSet(viewsets.ModelViewSet):
    queryset = EnvelopeFile.objects.all()
    serializer_class = EnvelopeFileSerializer
    permission_classes = (permissions.IsAuthenticated, )


class EnvelopeWorkflowViewSet(viewsets.ModelViewSet):
    queryset = BaseWorkflow.objects.all()
    serializer_class = NestedEnvelopeWorkflowSerializer
    permission_classes = (permissions.IsAuthenticated, )

