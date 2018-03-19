from edw.djutils import protected

from ..models import Envelope


class EnvelopeChannelTest(protected.views.ProtectedDetailView):
    """
    Test view for websocket notifications.
    Sets a cookie with the envelope's id for use with the Channels group,
    as a crude communication mechanism - the Vue component will already have the id available.
    """
    model = Envelope
    template_name = 'envelope_channel_test.html'

    def get(self, request, *args, **kwargs):
        envelope = self.get_object()
        response = super().get(request, *args, **kwargs)
        response.set_cookie('envelope_id', envelope.id)
        return response
