import logging
from channels.generic.websocket import JsonWebsocketConsumer
from asgiref.sync import AsyncToSync


log = logging.getLogger()
info = log.info
debug = log.debug
warn = log.warning
error = log.error


class EnvelopeWebsocketConsumer(JsonWebsocketConsumer):
    """Channels consumer for envelope notifications."""

    def get_envelope_group(self):
        """Builds envelope notifications group name."""
        envelope_id = self.scope['url_route']['kwargs'].get('pk')
        if envelope_id is None:
            return None
        return f'envelope_{envelope_id}'

    def connect(self):
        """
        Subscribes client to envelope's notifications group.
        Expects session to have the `envelope_id` cookie set.
        """
        group = self.get_envelope_group()

        if group is None:
            self.close()

        debug(f'Connecting client to envelope group: {group}')
        self.accept()
        AsyncToSync(self.channel_layer.group_add)(
                group,
                self.channel_name)

        AsyncToSync(self.channel_layer.group_send)(
                group,
                {
                    'type': 'envelope.system',
                    'data': f'Connected to channel {self.channel_name}'
                }
        )

    def disconnect(self, message):
        """Removes client from envelope's notifications group."""
        group = self.get_envelope_group()
        if group is not None:
            debug(f'Disconnecting channel {self.channel_name} from group: {group}')
            AsyncToSync(self.channel_layer.group_discard)(
                group, self.channel_name)

    def envelope_system(self, content):
        """Handler for non-business logic notifications."""
        self.send_json(
            {
                'event': 'system',
                'message': content['data']
            }
        )

    def envelope_entered_state(self, content):
        """Handler for state change notifications."""
        self.send_json(
            {
                'event': 'entered_state',
                'data': content['data']
            }
        )
