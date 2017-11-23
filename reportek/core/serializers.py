from rest_framework import serializers
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer

from .models import (
    Envelope, EnvelopeFile,
    ObligationGroup, ReportingPeriod,
    BaseWorkflow,
)


class EnvelopeFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnvelopeFile
        fields = ('id', 'name', 'file')
        read_only_fields = ('file', )


class NestedEnvelopeFileSerializer(NestedHyperlinkedModelSerializer,
                                   EnvelopeFileSerializer):
    parent_lookup_kwargs = {
        'envelope_pk': 'envelope__pk'
    }

    class Meta(EnvelopeFileSerializer.Meta):
        fields = ('url', ) + EnvelopeFileSerializer.Meta.fields
        extra_kwargs = {
            'url': {
                'view_name': 'api:envelope-file-detail',
            }
        }


class CreateEnvelopeFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnvelopeFile
        fields = ('file', )


class EnvelopeWorkflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseWorkflow
        fields = '__all__'


class NestedEnvelopeWorkflowSerializer(
        NestedHyperlinkedModelSerializer, EnvelopeWorkflowSerializer):

    parent_lookup_kwargs = {
        'envelope_pk': 'envelope__pk'
    }

    class Meta(EnvelopeWorkflowSerializer.Meta):
        fields = ['current_state', 'previous_state']
        extra_kwargs = {
            'url': {
                'view_name': 'api:envelope-workflow-detail',
            }
        }


class ReportingPeriodField(serializers.Serializer):
    def to_representation(self, obj):
        return {
            'id': obj.pk,
            'start': obj.period.lower,
            'end': obj.period.upper,
        }


class EnvelopeSerializer(serializers.ModelSerializer):
    obligation_group = serializers.PrimaryKeyRelatedField(
        queryset=ObligationGroup.objects.open()
    )
    reporting_period = ReportingPeriodField()
    files = NestedEnvelopeFileSerializer(many=True, read_only=True)
    workflow = NestedEnvelopeWorkflowSerializer(many=False, read_only=True)

    class Meta:
        model = Envelope
        fields = '__all__'
        read_only_fields = ('reporting_period', 'finalized')
