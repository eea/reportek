from rest_framework import serializers
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer

from .models import (
    Envelope, EnvelopeFile,
)


class EnvelopeFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnvelopeFile
        fields = '__all__'


class NestedEnvelopeFileSerializer(NestedHyperlinkedModelSerializer,
                                   EnvelopeFileSerializer):
    parent_lookup_kwargs = {
        'envelope_pk': 'envelope__pk'
    }


    class Meta(EnvelopeFileSerializer.Meta):
        fields = ['id', 'url', 'file']
        extra_kwargs = {
            'url': {
                'view_name': 'api:envelope-file-detail',
            }
        }


class EnvelopeSerializer(serializers.ModelSerializer):
    files = NestedEnvelopeFileSerializer(many=True, read_only=True)

    class Meta:
        model = Envelope
        fields = '__all__'
