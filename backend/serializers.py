import arrow
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from backend.models import Plant, Datapoint


class PlantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plant
        fields = ['id', 'name']


class DatapointSerializer(serializers.ModelSerializer):
    class Meta:
        model = Datapoint
        exclude = ['id', 'plant']


class PlantReportSerializer(PlantSerializer):
    datapoints = DatapointSerializer(many=True, read_only=True)

    class Meta(PlantSerializer.Meta):
        fields = PlantSerializer.Meta.fields + ['datapoints']


class DatapointImportSerializer(DatapointSerializer):
    def to_internal_value(self, data):
        try:
            result = {
                'timestamp': arrow.get(data['datetime']).datetime,
                'energy_expected': data['expected']['energy'],
                'energy_observed': data['observed']['energy'],
                'irradiation_expected': data['expected']['irradiation'],
                'irradiation_observed': data['observed']['irradiation'],
            }
        except:
            raise ValidationError({"message": f"Unrecognized datapoint item"})
        return super().to_internal_value(result)
