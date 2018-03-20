from .base import BaseWSConsumer


class EnvelopeWSConsumer(BaseWSConsumer):
    """Channels consumer for envelope notifications."""

    TOPIC = 'envelope'
    EVENTS = (
        'entered_state',
        'added_file',
        'changed_file',
        'deleted_file',
    )

    def get_group(self):
        """Builds per-envelope notifications group name."""
        envelope_id = self.scope['url_route']['kwargs'].get('pk')
        if envelope_id is None:
            return None
        return f'envelope_{envelope_id}'
