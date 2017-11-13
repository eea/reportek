from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder


class TransitionEvent(models.Model):
    """
    Transition events in a workflow's life cycle.
    """
    timestamp = models.DateTimeField(auto_now_add=True, editable=False)

    # Use generic FKs to accomodate the various workflow types
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    transition = models.CharField(max_length=60)
    from_state = models.CharField(max_length=60)
    to_state = models.CharField(max_length=60)
    extra = JSONField(encoder=DjangoJSONEncoder, null=True)

    class Meta:
        verbose_name = 'workflow event'
        unique_together = ('timestamp', 'object_id', 'from_state', 'to_state')
