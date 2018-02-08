from rest_framework import serializers

from reportek.roles.models import User
from reportek.core.models import (
    Instrument, Client, Reporter,
    Obligation, ObligationSpec,
    ReportingCycle, ReporterSubdivision,
    Envelope,
)


class ReporterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reporter
        fields = ('abbr', 'name')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'role')


class ReporterUserSerializer(serializers.ModelSerializer):
    reporter = ReporterSerializer()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('reporter',)


class InstrumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instrument
        fields = (
            'id', 'rod_url',
            'title',
        )


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = (
            'id', 'rod_url',
            'name', 'abbr',
        )


class ReporterSubdivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReporterSubdivision
        fields = (
            'id', 'rod_url',
            'name',
        )


class BaseReportingCycleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportingCycle
        fields = (
            'id', 'rod_url',
            'reporting_start_date', 'reporting_end_date',
        )

class ObligationReportingCycleSerializer(BaseReportingCycleSerializer):
    reporter_subdivisions = ReporterSubdivisionSerializer(many=True,
                                                          source='subdivisions')

    class Meta(BaseReportingCycleSerializer.Meta):
        fields = BaseReportingCycleSerializer.Meta.fields + (
            'reporter_subdivisions',
        )


class BaseObligationSerializer(serializers.ModelSerializer):
    instrument = InstrumentSerializer()
    client = ClientSerializer()

    class Meta:
        model = Obligation
        fields = (
            'id', 'rod_url',
            'title', 'description',
            'instrument', 'client',
        )


class PendingObligationSerializer(serializers.ModelSerializer):
    reporting_cycles = ObligationReportingCycleSerializer(many=True,
                                                          source='cycles')

    class Meta(BaseObligationSerializer.Meta):
        fields = BaseObligationSerializer.Meta.fields + (
            'reporting_cycles',
        )


class EnvelopeSerializer(serializers.ModelSerializer):
    obligation = BaseObligationSerializer(read_only=True)
    reporting_cycle = BaseReportingCycleSerializer()
    reporter_subdivision = ReporterSubdivisionSerializer()

    class Meta:
        model = Envelope
        fields = (
            'id', 'name', 'obligation',
            'reporting_cycle', 'reporter_subdivision',
        )


class EnvelopeReportingCycle(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return ReportingCycle.objects.open().for_reporter(
            self.context['request'].user.reporter
        )


class EnvelopeReporterSubdivision(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        # TODO: this queryset is not enough. it must be trimmed down
        # based on the ReportingCycle.
        subdivisions = ReporterSubdivision.objects.for_reporter(
            self.context['request'].user.reporter
        )
        return subdivisions


class CreateEnvelopeSerializer(EnvelopeSerializer):
    reporting_cycle = EnvelopeReportingCycle()
    reporter_subdivision = EnvelopeReporterSubdivision(required=False, allow_null=True)
