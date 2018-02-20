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


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    http://www.django-rest-framework.org/api-guide/serializers/#dynamically-modifying-fields
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


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


class ReportingCycleDetailsSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = ReportingCycle
        fields = '__all__'


class ReportingCycleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportingCycle
        fields = ('id', 'obligation', 'obligation_spec',
                  'reporting_start_date', 'reporting_end_date',
                  'is_open', 'rod_url', 'created_at', 'updated_at')


class ObligationSpecSerializer(serializers.ModelSerializer):
    reporting_cycles = ReportingCycleSerializer(many=True, read_only=True)

    class Meta:
        model = ObligationSpec
        fields = ('id', 'obligation_id', 'version', 'is_current', 'draft',
                  'schema', 'workflow_class', 'qa_xmlrpc_uri', 'reporting_cycles',
                  'rod_url', 'created_at', 'updated_at',)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['reporting_cycles'] = ReportingCycleDetailsSerializer(
            instance.reporting_cycles.all(),
            many=True,
            fields=('id', 'reporting_start_date', 'reporting_end_date', 'is_open')
        ).data
        return data


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


class PendingReportingCycleSerializer(serializers.ModelSerializer):

    subdivisions = ReporterSubdivisionSerializer(many=True)

    class Meta:
        model = ReportingCycle
        fields = ('id', 'reporting_start_date', 'reporting_end_date',
                  'is_open', 'rod_url', 'created_at', 'updated_at',
                  'subdivisions')


class PendingObligationSerializer(serializers.ModelSerializer):

    reporting_cycles = PendingReportingCycleSerializer(many=True)

    class Meta:
        model = Obligation
        fields = ('id', 'title', 'description', 'instrument', 'terminated',
                  'client', 'active_since', 'active_until', 'reporting_duration',
                  'reporting_frequency', 'rod_url', 'created_at',
                  'updated_at', 'reporting_cycles')


class EnvelopeFileSerializer(serializers.ModelSerializer):
    uploader = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = EnvelopeFile
        fields = ('id', 'name', 'file', 'restricted', 'uploader')
        read_only_fields = ('file', 'uploader')


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
        fields = ('file', 'uploader')


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
        fields = ('current_state', 'previous_state',
                  'available_transitions', 'upload_allowed',
                  )
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
        fields = ('id', 'created_at', 'token', 'filename', 'tus_id')
        extra_kwargs = {
            'url': {
                'view_name': 'api:envelope-token-detail',
            }
        }


class EnvelopeSerializer(serializers.ModelSerializer):
    files = NestedEnvelopeFileSerializer(many=True, read_only=True)
    workflow = NestedEnvelopeWorkflowSerializer(many=False, read_only=True)

    class Meta:
        model = Envelope
        fields = '__all__'
        read_only_fields = (
            'workflow',
            'finalized',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['reporting_cycle'] = ReportingCycleDetailsSerializer(
            instance.reporting_cycle,
            many=False,
            fields=('id', 'reporting_start_date', 'reporting_end_date', 'is_open')
        ).data
        return data


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
