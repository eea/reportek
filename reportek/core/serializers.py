from django.conf import settings
from rest_framework import serializers
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer

from django.contrib.auth.models import Group

from rest_framework.authtoken.models import Token

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
    Envelope, EnvelopeFile, EnvelopeOriginalFile,
    BaseWorkflow,
    UploadToken,
    QAJob,
    QAJobResult,
    ReportekUser,
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


class PendingObligationSpecSerializer(serializers.ModelSerializer):

    class Meta:
        model = ObligationSpec
        fields = ('id', 'version', 'is_current', 'draft', 'schema',
                  'workflow_class', 'rod_url', 'created_at', 'updated_at')


class PendingReportingCycleSerializer(serializers.ModelSerializer):

    subdivisions = ReporterSubdivisionSerializer(many=True)
    obligation_spec = PendingObligationSpecSerializer()

    class Meta:
        model = ReportingCycle
        fields = ('id', 'reporting_start_date', 'reporting_end_date',
                  'is_open', 'rod_url', 'created_at', 'updated_at',
                  'obligation_spec', 'subdivisions')


class PendingObligationSerializer(serializers.ModelSerializer):

    reporting_cycles = PendingReportingCycleSerializer(many=True)

    class Meta:
        model = Obligation
        fields = ('id', 'title', 'description', 'instrument', 'terminated',
                  'client', 'active_since', 'active_until', 'reporting_duration',
                  'reporting_frequency', 'rod_url', 'created_at',
                  'updated_at', 'reporting_cycles')


class EnvelopeOriginalFileSerializer(serializers.ModelSerializer):

    content_url = serializers.SerializerMethodField()

    class Meta:
        model = EnvelopeOriginalFile
        fields = ('id', 'name', 'content_url', 'uploader', 'size', 'created', 'updated')
        read_only_fields = ('content_url', 'uploader', 'size', 'created', 'updated')

    @staticmethod
    def get_content_url(obj):
        return obj.fq_download_url


class NestedEnvelopeOriginalFileSerializer(NestedHyperlinkedModelSerializer,
                                           EnvelopeOriginalFileSerializer):
    parent_lookup_kwargs = {
        'envelope_pk': 'envelope__pk'
    }

    class Meta(EnvelopeOriginalFileSerializer.Meta):
        fields = ('url', ) + EnvelopeOriginalFileSerializer.Meta.fields
        extra_kwargs = {
            'url': {
                'view_name': 'api:envelope-original-file-detail',
            }
        }


class CreateEnvelopeOriginalFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnvelopeOriginalFile
        fields = ('file', )


class EnvelopeFileSerializer(serializers.ModelSerializer):
    uploader = serializers.PrimaryKeyRelatedField(read_only=True)
    content_url = serializers.SerializerMethodField()

    class Meta:
        model = EnvelopeFile
        fields = ('id', 'name', 'content_url', 'restricted', 'uploader', 'size', 'created', 'updated')
        read_only_fields = ('content', 'uploader', 'size', 'created', 'updated')

    @staticmethod
    def get_content_url(obj):
        return obj.fq_download_url


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
                  'updated_at',
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
    envelopefiles = NestedEnvelopeFileSerializer(many=True, read_only=True)
    envelopeoriginalfiles = NestedEnvelopeOriginalFileSerializer(many=True, read_only=True)
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


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('name',)


class WorkspaceReporterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reporter
        fields = ('id', 'name', 'abbr')


class WorkspaceUserSerializer(serializers.ModelSerializer):
    groups = serializers.SerializerMethodField()
    ldap_groups = serializers.SerializerMethodField()
    effective_groups = serializers.SerializerMethodField()
    reporters = serializers.SerializerMethodField()

    @staticmethod
    def get_reporters(obj):
        if not obj.is_authenticated():
            return []
        return [WorkspaceReporterSerializer(r).data for r in obj.get_reporters()]

    @staticmethod
    def get_groups(obj):
        return sorted([g.name for g in obj.groups.all()])

    @staticmethod
    def get_ldap_groups(obj):
        if not obj.is_authenticated():
            return []
        return sorted([g.name for g in obj.ldap_groups])

    @staticmethod
    def get_effective_groups(obj):
        if not obj.is_authenticated():
            return []
        return sorted([g.name for g in obj.effective_groups])

    class Meta:
        model = ReportekUser
        fields = ('username', 'first_name', 'last_name', 'email',
                  'groups', 'ldap_groups', 'effective_groups',
                  'reporters')


class WorkspaceEnvelopeSerializer(EnvelopeSerializer):
    envelopefiles = EnvelopeFileSerializer(many=True, read_only=True)
    obligation = serializers.SerializerMethodField()

    @staticmethod
    def get_obligation(obj):
        return WorkspaceObligationSerializer(obj.obligation_spec.obligation).data


class WorkspaceObligationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Obligation
        fields = ('id', 'title')


class AuthTokenByValueSerializer(serializers.ModelSerializer):
    token = serializers.SerializerMethodField()
    expires = serializers.SerializerMethodField()

    class Meta:
        model = Token
        fields = ('token', 'created', 'expires')

    @staticmethod
    def get_token(obj):
        return obj.key

    @staticmethod
    def get_expires(obj):
        return obj.created + settings.TOKEN_EXPIRE_INTERVAL
