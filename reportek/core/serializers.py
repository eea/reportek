from rest_framework import serializers
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer

from .models import (
    Instrument,
    Client,
    Reporter,
    ReporterSubdivisionCategory,
    ReporterSubdivision,
    Obligation,
    ObligationSpec,
    ObligationSpecReporter,
    ReportingCycle,
    Envelope, EnvelopeFile,
    BaseWorkflow,
    UploadToken,
    QAJob,
    QAJobResult,
)


def get_field_names(model):
    return tuple([f.name for f in model._meta.fields])


class InstrumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instrument
        fields = ('id', 'title', 'rod_url', 'created_at', 'updated_at')


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ('id', 'name', 'abbr', 'rod_url', 'created_at', 'updated_at')


class ReporterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reporter
        fields = ('id', 'name', 'abbr', 'slug', 'rod_url',
                  'subdivision_categories', 'created_at', 'updated_at')


class ReporterSubdivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReporterSubdivision
        fields = ('id', 'name', 'rod_url', 'created_at', 'updated_at')


class NestedReporterSubdivisionSerializer(NestedHyperlinkedModelSerializer,
                                          ReporterSubdivisionSerializer):

    parent_lookup_kwargs = {
        'category_pk': 'category__pk'
    }

    class Meta(ReporterSubdivisionSerializer.Meta):
        fields = ('url', ) + ReporterSubdivisionSerializer.Meta.fields
        extra_kwargs = {
            'url': {
                'view_name': 'api:subdivision-detail',
            }
        }


class ReporterSubdivisionCategorySerializer(serializers.ModelSerializer):
    subdivisions = NestedReporterSubdivisionSerializer(many=True, read_only=True)

    class Meta:
        model = ReporterSubdivisionCategory
        fields = ('id', 'name', 'reporter', 'subdivisions', 'rod_url',
                  'created_at', 'updated_at',)


class ObligationSpecSerializer(serializers.ModelSerializer):
    class Meta:
        model = ObligationSpec
        fields = ('id', 'obligation_id', 'version', 'is_current', 'draft',
                  'schema', 'workflow_class', 'qa_xmlrpc_uri',
                  'rod_url', 'created_at', 'updated_at',)


class NestedObligationSpecSerializer(NestedHyperlinkedModelSerializer,
                                     ObligationSpecSerializer):

    parent_lookup_kwargs = {
        'obligation_pk': 'obligation__pk'
    }

    class Meta(ObligationSpecSerializer.Meta):
        fields = ('url', ) + ObligationSpecSerializer.Meta.fields
        extra_kwargs = {
            'url': {
                'view_name': 'api:obligation-spec-detail',
            }
        }


class ObligationSpecReporterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ObligationSpecReporter
        fields = ('id', 'spec', 'reporter', 'subdivision_category',
                  'rod_url', 'created_at', 'updated_at',)


class ObligationSerializer(serializers.ModelSerializer):

    specs = NestedObligationSpecSerializer(many=True, read_only=True)

    class Meta:
        model = Obligation
        fields = ('id', 'title', 'description', 'instrument', 'terminated',
                  'client', 'active_since', 'active_until', 'reporting_duration',
                  'reporting_frequency', 'specs', 'rod_url', 'created_at',
                  'updated_at',)


class ReportingCycleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportingCycle
        fields = ('id', 'obligation', 'obligation_spec',
                  'reporting_start_date', 'reporting_end_date',
                  'is_open', 'rod_url', 'created_at', 'updated_at')


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


class UploadTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadToken
        fields = '__all__'


class NestedUploadTokenSerializer(
        NestedHyperlinkedModelSerializer, UploadTokenSerializer):

    parent_lookup_kwargs = {
        'envelope_pk': 'envelope__pk'
    }

    class Meta(UploadTokenSerializer.Meta):
        fields = ['id', 'created_at', 'token', 'filename', 'tus_id']
        extra_kwargs = {
            'url': {
                'view_name': 'api:envelope-token-detail',
            }
        }


class EnvelopeSerializer(serializers.ModelSerializer):
    # obligation_spec = serializers.PrimaryKeyRelatedField(
    #     queryset=ObligationSpec.objects.open()
    # )
    files = NestedEnvelopeFileSerializer(many=True, read_only=True)
    workflow = NestedEnvelopeWorkflowSerializer(many=False, read_only=True)

    class Meta:
        model = Envelope
        fields = '__all__'
        read_only_fields = ('obligation_spec', 'reporting_cycle', 'finalized')


class QAJobResultSerializer(serializers.ModelSerializer):
    code = serializers.CharField(source='get_code_display')
    feedback_status = serializers.CharField(source='get_feedback_status_display')

    class Meta:
        model = QAJobResult
        fields = '__all__'


class QAJobSerializer(serializers.ModelSerializer):
    latest_result = QAJobResultSerializer(read_only=True)

    class Meta:
        model = QAJob
        fields = ['latest_result'] + [f.name for f in QAJob._meta.fields]
