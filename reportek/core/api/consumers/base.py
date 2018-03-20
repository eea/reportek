import logging
from functools import partial
from channels.generic.websocket import JsonWebsocketConsumer
from asgiref.sync import AsyncToSync

log = logging.getLogger()
info = log.info
debug = log.debug
warn = log.warning
error = log.error


class BaseWSConsumer(JsonWebsocketConsumer):
    """
    Base Channels consumer for topic group notifications.

    Concrete consumer implementations must set `TOPIC` to a unique string that
    will be matched with event domains (e.g. 'envelope' to catch events like
    'envelope.entered_state').

    Automatic default handling is provided for events listed in the `EVENTS`
    tuple, plus the 'system' event used for connection details notifications.
    Consumers can override the default handling by implementing concrete event
    handlers.
    """

    # Concrete consumers must set this to a string, e.g. 'envelopes'
    TOPIC = None

    # Concrete consumers must set this to a tuple of event names (without the topic)
    EVENTS = ()

    def __getattr__(self, item):
        allowed_topic = self.TOPIC or ''
        allowed_events = self.EVENTS or ()

        allowed_events += ('system',)
        topic, _, event = item.partition('_')
        if topic == allowed_topic and event in allowed_events:
            debug(f'Creating partial handler for WS event: "{topic}.{event}"')
            return partial(self._auto_event_handler, event=event)

        return super().__getattribute__(item)

    def _auto_event_handler(self, content, event):
        self.send_json(
            {
                'event': event,
                'data': content.get('data')
            }
        )

    def get_group(self):
        """
        Child classes must implement this to return the name of the
        specific notifications group, e.g. 'envelope_17'.
        """
        raise NotImplementedError

    def connect(self):
        """Subscribes client to the notifications group."""
        group = self.get_group()

        if group is None:
            self.close()

        self.accept()
        AsyncToSync(self.channel_layer.group_add)(
                group,
                self.channel_name)

        AsyncToSync(self.channel_layer.group_send)(
                group,
                {
                    'type': f'{self.TOPIC}.system',
                    'data': f'Connected to channel {self.channel_name}'
                }
        )

    def disconnect(self, message):
        """Removes client from the notifications group."""
        group = self.get_group()
        if group is not None:
            AsyncToSync(self.channel_layer.group_discard)(
                group, self.channel_name)
