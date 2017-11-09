from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder

from reportek.core.models.workflows import (
    WFTransition,
    WFState
)


class ReportLog(models.Model):
    """
    Log for events in a report's life cycle.
    Currently dedicated to transitions logging.
    """
    timestamp = models.DateTimeField(auto_now_add=True, editable=False)

    # We use generic FKs to accomodate the various report types
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    transition = models.ForeignKey(WFTransition)
    from_state = models.ForeignKey(WFState, related_name='in_log_events_from')
    to_state = models.ForeignKey(WFState, related_name='in_log_events_to')
    extra = JSONField(encoder=DjangoJSONEncoder, null=True)

    class Meta:
        verbose_name = 'report log event'
        unique_together = ('timestamp', 'from_state', 'to_state')
