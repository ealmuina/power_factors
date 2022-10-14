from http import HTTPStatus

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from backend.models import Plant
from backend.serializers import PlantSerializer, PlantReportSerializer
from backend.tasks import PollPlantMonitoringData
from backend.utils import parse_date


class PlantViewSet(viewsets.ModelViewSet):
    queryset = Plant.objects.order_by('id')
    serializer_class = PlantSerializer

    @action(detail=False)
    def report(self, request):
        self.serializer_class = PlantReportSerializer
        return self.list(request)

    @action(detail=False, methods=['POST'])
    def pull_datapoints(self, request):
        plants = Plant.objects.all()

        # Get and validate list of plant IDs
        plant_ids = request.data.get('plant_ids')
        if plant_ids:
            valid_ids = plants.filter(id__in=plant_ids).values_list('id', flat=True)
            invalid_ids = set(plant_ids) - set(valid_ids)
            if invalid_ids:
                raise ValidationError(f'Invalid plant IDs: {invalid_ids}')
        else:
            plant_ids = plants.values_list('id', flat=True)

        # Get and validate dates
        date_from = parse_date(request.data.get('from'), validate=True)
        date_to = parse_date(request.data.get('to'), validate=True)

        # Launch task for each plant
        for plant_id in plant_ids:
            PollPlantMonitoringData.delay(
                plant_id=plant_id,
                date_from=date_from,
                date_to=date_to
            )
        return Response(status=HTTPStatus.OK)
