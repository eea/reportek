from rest_framework import viewsets, status
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from ..models import (
    Envelope,
    EnvelopeFile,
    BaseWorkflow,
)
from ..serializers import (
    EnvelopeSerializer,
    EnvelopeFileSerializer,
    NestedEnvelopeWorkflowSerializer
)
from .. import permissions


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

        def make_response(with_error=None):
            response = {
                'transition': transition_name,
                'current_state': workflow.current_state,
            }
            if with_error:
                response['error'] = with_error
            return response

        try:
            transition = getattr(workflow.xwf, transition_name)
        except AttributeError:
            return Response(
                make_response(with_error='Invalid transition name'),
                status=status.HTTP_400_BAD_REQUEST
            )

        if not transition.is_available():
            return Response(
                make_response(with_error='Transition not allowed from current state'),
                status=status.HTTP_406_NOT_ACCEPTABLE
            )

        try:
            transition()
        except Exception as err:
            return Response(
                make_response(with_error=err),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(make_response())

    @detail_route(methods=['get'])
    def history(self, request, pk):
        """
        Returns an evelope's transition history.
        """
        envelope = self.get_object()
        workflow = envelope.workflow
        return Response(
            {
                ev.timestamp.isoformat(): {
                    'transition': ev.transition,
                    'from_state': ev.from_state,
                    'to_state': ev.to_state
                }
                for ev in workflow.history.all()
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
