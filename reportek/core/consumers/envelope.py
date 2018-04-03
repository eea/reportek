from enum import Enum, auto
from .base import BaseWSConsumer


class EnvelopeEvents(Enum):
    ENTERED_STATE = auto()

    ADDED_FILE = auto()
    CHANGED_FILE = auto()
    DELETED_FILE = auto()

    ADDED_ORIGINAL_FILE = auto()
    CHANGED_ORIGINAL_FILE = auto()
    DELETED_ORIGINAL_FILE = auto()

    ADDED_SUPPORT_FILE = auto()
    CHANGED_SUPPORT_FILE = auto()
    DELETED_SUPPORT_FILE = auto()

    RECEIVED_AUTO_QA_FEEDBACK = auto()
    COMPLETED_AUTO_QA = auto()


class EnvelopeWSConsumer(BaseWSConsumer):
    """Channels consumer for envelope notifications."""

    TOPIC = 'envelope'
    EVENTS = EnvelopeEvents

    def get_group(self):
        """Builds per-envelope notifications group name."""
        envelope_id = self.scope['url_route']['kwargs'].get('pk')
        if envelope_id is None:
            return None
        return f'envelope_{envelope_id}'
