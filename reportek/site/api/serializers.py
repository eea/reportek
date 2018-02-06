from rest_framework import serializers

from reportek.core.models import (
    Instrument, Client,
    Obligation, ObligationSpec,
    ReportingCycle, ReporterSubdivision,
)


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


class ReportingCycleSerializer(serializers.ModelSerializer):
    subdivisions = ReporterSubdivisionSerializer(many=True)

    class Meta:
        model = ReportingCycle
        fields = (
            'id', 'rod_url',
            'reporting_start_date', 'reporting_end_date',
            'subdivisions',
        )


class ObligationSerializer(serializers.ModelSerializer):
    cycles = ReportingCycleSerializer(many=True)
    instrument = InstrumentSerializer()
    client = ClientSerializer()

    class Meta:
        model = Obligation
        fields = (
            'id', 'rod_url',
            'title', 'description',
            'instrument', 'client', 'cycles',
        )
