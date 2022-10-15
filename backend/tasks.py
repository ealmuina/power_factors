import datetime
import logging
from http import HTTPStatus
from typing import List, Tuple, Optional

import pytz
import requests
from django.conf import settings
from django.utils import timezone

from backend.models import Plant, Datapoint
from backend.serializers import DatapointImportSerializer
from power_factors.celery import app


@app.task(ignore_result=True)
def poll_monitoring_data():
    """
    Launch a polling task for each Plant.
    """
    for plant_id in Plant.objects.all().values_list('id', flat=True):
        PollPlantMonitoringData.delay(plant_id)


class PollPlantMonitoringData(app.Task):
    """
    Polling task for a given Plant.
    """
    ignore_result = True
    serializer = 'pickle'

    MONITORING_SERVICE_ADDRESS = 'http://monitoring:5000'
    DEFAULT_POLLING_FROM_DATE = datetime.datetime(
        2022, 1, 1,
        tzinfo=pytz.timezone(settings.TIME_ZONE)
    )
    MAX_POLLING_ATTEMPTS = 3

    def _get_next_unregistered_date(self, plant_id) -> datetime.date:
        """
        Get the next date for which there are no Datapoints registered for a given Plant.
        :param plant_id: Plant ID
        :return: Next date with unregistered Datapoints
        """
        last_timestamp = Datapoint.objects.filter(
            plant_id=plant_id
        ).order_by(
            'timestamp'
        ).values_list('timestamp', flat=True).last()

        last_timestamp = last_timestamp or self.DEFAULT_POLLING_FROM_DATE
        return last_timestamp.date() + datetime.timedelta(days=1)

    def _request_monitoring_data(
            self,
            plant_id,
            date_from: datetime.date,
            date_to: datetime.date
    ) -> List[dict]:
        """
        Make a request to the monitoring service.
        :param plant_id: Plant ID
        :param date_from: Start date
        :param date_to: End date
        :return: Monitoring service response
        """
        # Make request up to MAX_POLLING_ATTEMPTS times
        attempts = 0
        while attempts < self.MAX_POLLING_ATTEMPTS:
            attempts += 1
            response = requests.get(
                self.MONITORING_SERVICE_ADDRESS,
                params={
                    'plant-id': plant_id,
                    'from': date_from,
                    'to': date_to
                }
            )
            # Check if response is correct
            if response.status_code == HTTPStatus.OK:
                data = response.json()
                if isinstance(data, list):
                    return data
        return []

    @staticmethod
    def _parse_datapoints(data: List[dict]) -> List[dict]:
        """
        Parse a list of datapoints received from the monitoring service.
        :param data: List of datapoints.
        :return: Valid datapoints list, parsed to match the Datapoint model schema
        """
        valid_datapoints = []
        for item in data:
            serializer = DatapointImportSerializer(data=item)
            if serializer.is_valid():
                valid_datapoints.append(serializer.validated_data)
            else:
                logging.error({
                    'message': 'Unable to store invalid datapoint',
                    'item': item,
                    'errors': serializer.errors
                })
        return valid_datapoints

    @staticmethod
    def _split_datapoints(plant_id, data: List[dict]) -> Tuple[List[Datapoint], List[Datapoint]]:
        """
        Split parsed datapoints in two lists: those to be created and updated respectively
        :param plant_id: Plant ID
        :param data: List of datapoints
        :return: Tuple with two elements:
            - datapoints to create: List of Datapoint instances ready for creation in DB.
            - datapoints to update: List of Datapoint instances ready for updating in DB.
        """
        # Get Datapoints from DB that match the parsed list
        datapoints = Datapoint.objects.filter(
            plant_id=plant_id,
            timestamp__in=map(lambda dp: dp['timestamp'], data)
        )
        datapoints_by_timestamp = {
            dp.timestamp: dp
            for dp in datapoints
        }

        datapoints_to_create, datapoints_to_update = [], []
        for item in data:
            dp = datapoints_by_timestamp.get(item['timestamp'])
            if dp:
                # Found an item corresponding to the same plant and timestamp
                # Update it!
                for key, value in item.items():
                    setattr(dp, key, value)
                datapoints_to_update.append(dp)
            else:
                # No matching datapoint found
                # Create a new one!
                datapoints_to_create.append(Datapoint(
                    plant_id=plant_id,
                    **item
                ))

        return datapoints_to_create, datapoints_to_update

    def run(
            self,
            plant_id,
            date_from: Optional[datetime.date] = None,
            date_to: Optional[datetime.date] = None
    ):
        """
        Given a plant id and a dates range, pull datapoints from the monitoring service.
        :param plant_id: Plant ID
        :param date_from: Start date. Defaults to next date with no records yet.
        :param date_to: End date. Defaults to today.
        """
        date_from = date_from or self._get_next_unregistered_date(plant_id)
        date_to = date_to or timezone.now().date()

        # Process data in batches of 1 year
        cursor = date_from
        while cursor < date_to:
            # Get datapoints from monitoring service
            data = self._request_monitoring_data(
                plant_id=plant_id,
                date_from=cursor,
                date_to=min(date_to, cursor + datetime.timedelta(days=365))
            )
            # Parse datapoints
            valid_datapoints = self._parse_datapoints(data)
            # Create or update as corresponds
            datapoints_to_create, datapoints_to_update = self._split_datapoints(plant_id, valid_datapoints)
            Datapoint.objects.bulk_create(datapoints_to_create)
            Datapoint.objects.bulk_update(
                objs=datapoints_to_update,
                fields=['energy_expected', 'energy_observed', 'irradiation_expected', 'irradiation_observed']
            )
            cursor += datetime.timedelta(days=365)

    def run_alternative(self, plant_id, date_from=None, date_to=None):
        date_from = date_from or self._get_next_unregistered_date(plant_id)
        date_to = date_to or timezone.now().date()

        cursor = date_from
        while cursor < date_to:
            data = self._request_monitoring_data(
                plant_id=plant_id,
                date_from=cursor,
                date_to=min(date_to, cursor + datetime.timedelta(days=365))
            )
            for item in data:
                serializer = DatapointImportSerializer(data=item)
                if serializer.is_valid():
                    validated_data = serializer.validated_data
                    Datapoint.objects.get_or_create(
                        plant_id=plant_id,
                        timestamp=validated_data.pop('timestamp'),
                        defaults=validated_data
                    )
                else:
                    logging.error({
                        'message': 'Unable to store invalid datapoint',
                        'item': item,
                        'errors': serializer.errors
                    })
            cursor += datetime.timedelta(days=365)


PollPlantMonitoringData = app.register_task(PollPlantMonitoringData())
