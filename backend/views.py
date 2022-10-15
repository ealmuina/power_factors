from http import HTTPStatus

from django.db.models import Prefetch
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from backend.models import Plant, Datapoint
from backend.serializers import PlantSerializer, PlantReportSerializer
from backend.tasks import PollPlantMonitoringData
from backend.utils import parse_date, parse_ids


class PlantViewSet(viewsets.ModelViewSet):
    queryset = Plant.objects.order_by('id')
    serializer_class = PlantSerializer

    @action(detail=False)
    def report(self, request):
        # Get and validate list of plant IDs
        plant_ids = parse_ids(
            model=Plant,
            id_list=request.GET.getlist('plant_ids', [])
        )
        # Get and validate dates
        date_from = parse_date(request.GET.get('from'), as_datetime=True)
        date_to = parse_date(request.GET.get('to'), as_datetime=True)

        conditions = {}
        if date_from:
            conditions['timestamp__gte'] = date_from
        if date_to:
            conditions['timestamp__lt'] = date_to

        # Filter queryset by plant IDs and date ranges
        self.queryset = self.queryset.filter(
            id__in=plant_ids
        ).prefetch_related(
            Prefetch(
                'datapoints',
                queryset=Datapoint.objects.filter(**conditions).order_by('timestamp')
            )
        )
        self.serializer_class = PlantReportSerializer
        return self.list(request)

    @action(detail=False, methods=['POST'])
    def pull_datapoints(self, request):
        # Get and validate list of plant IDs
        plant_ids = parse_ids(
            model=Plant,
            id_list=request.data.get('plant_ids', [])
        )
        # Get and validate dates
        date_from = parse_date(request.data.get('from'))
        date_to = parse_date(request.data.get('to'))

        # Launch task for each plant
        for plant_id in plant_ids:
            PollPlantMonitoringData.delay(
                plant_id=plant_id,
                date_from=date_from,
                date_to=date_to
            )
        return Response(status=HTTPStatus.OK)
