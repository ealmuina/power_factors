import datetime
from http import HTTPStatus
from unittest.mock import patch

import pytz
from django.conf import settings
from django.test import TestCase

from backend.models import Plant, Datapoint
from backend.tasks import PollPlantMonitoringData


class PollMonitoringTestCase(TestCase):
    def setUp(self):
        self.existent_plant = Plant.objects.create(
            name='existent-plant'
        )

    @patch('backend.tasks.requests.get')
    def test_poll_task(self, mock_get):
        """Poll task successfully creates datapoints"""
        mock_get.return_value.status_code = HTTPStatus.OK
        mock_get.return_value.json.return_value = [
            {
                "datetime": "2019-01-01T00:00:00",
                "expected": {
                    "energy": 87.55317774223157,
                    "irradiation": 98.19878838432548
                },
                "observed": {
                    "energy": 90.78559770167864,
                    "irradiation": 30.085498370965905
                }
            },
            {
                "datetime": "2019-01-01T01:00:00",
                "expected": {
                    "energy": 87.55317774223157,
                    "irradiation": 98.19878838432548
                },
                "observed": {
                    "energy": 90.78559770167864,
                    "irradiation": 30.085498370965905
                }
            }
        ]
        PollPlantMonitoringData(plant_id=self.existent_plant.id)
        response = self.client.get('/plants/report/')
        data = response.json()
        datapoints = data['results'][0]['datapoints']
        self.assertEqual(
            datapoints,
            [
                {
                    'timestamp': '2019-01-01T00:00:00Z',
                    "energy_expected": 87.55317774223157,
                    "energy_observed": 90.78559770167864,
                    "irradiation_expected": 98.19878838432548,
                    "irradiation_observed": 30.085498370965905
                },
                {
                    'timestamp': '2019-01-01T01:00:00Z',
                    "energy_expected": 87.55317774223157,
                    "energy_observed": 90.78559770167864,
                    "irradiation_expected": 98.19878838432548,
                    "irradiation_observed": 30.085498370965905
                }
            ]
        )

    @patch('backend.tasks.requests.get')
    def test_poll_task_bad_status_code(self, mock_get):
        """Monitoring service returns a bad status code. No datapoints are created"""
        mock_get.return_value.status_code = HTTPStatus.SERVICE_UNAVAILABLE
        PollPlantMonitoringData(plant_id=self.existent_plant.id)
        self.assertFalse(Datapoint.objects.exists())

    @patch('backend.tasks.requests.get')
    def test_poll_task_bad_response(self, mock_get):
        """Monitoring service returns an error message. No datapoints are created"""
        mock_get.return_value.status_code = HTTPStatus.OK
        mock_get.return_value.json.return_value = {
            'error': 'Service error'
        }
        PollPlantMonitoringData(plant_id=self.existent_plant.id)
        self.assertFalse(Datapoint.objects.exists())

    @patch('backend.tasks.requests.get')
    def test_poll_task_corrupt_data(self, mock_get):
        """Some points are corrupted in monitoring service response. Only valid datapoints are created"""
        mock_get.return_value.status_code = HTTPStatus.OK
        mock_get.return_value.json.return_value = [
            {
                "datetime": "2019-01-01T00:00:00",
                "expected": {
                    "energy": 87.55317774223157,
                    "irradiation": 98.19878838432548
                }
                # 'observed' values missing
            },
            {
                "datetime": "2019-01-01T01:00:00",
                "expected": {
                    "energy": 87.55317774223157,
                    "irradiation": 98.19878838432548
                },
                "observed": {
                    "energy": 90.78559770167864,
                    "irradiation": 30.085498370965905
                }
            }
        ]
        PollPlantMonitoringData(plant_id=self.existent_plant.id)
        response = self.client.get('/plants/report/')
        data = response.json()
        datapoints = data['results'][0]['datapoints']
        self.assertEqual(
            datapoints,
            [
                {
                    'timestamp': '2019-01-01T01:00:00Z',
                    "energy_expected": 87.55317774223157,
                    "energy_observed": 90.78559770167864,
                    "irradiation_expected": 98.19878838432548,
                    "irradiation_observed": 30.085498370965905
                }
            ]
        )

    @patch('backend.tasks.requests.get')
    def test_poll_task_update(self, mock_get):
        """Datapoint downloaded already exists, so it gets updated"""
        Datapoint.objects.create(
            plant=self.existent_plant,
            timestamp=datetime.datetime(2019, 1, 1, hour=1, tzinfo=pytz.timezone(settings.TIME_ZONE)),
            energy_expected=0,
            energy_observed=0,
            irradiation_expected=0,
            irradiation_observed=0
        )
        mock_get.return_value.status_code = HTTPStatus.OK
        mock_get.return_value.json.return_value = [
            {
                "datetime": "2019-01-01T01:00:00",
                "expected": {
                    "energy": 87.55317774223157,
                    "irradiation": 98.19878838432548
                },
                "observed": {
                    "energy": 90.78559770167864,
                    "irradiation": 30.085498370965905
                }
            }
        ]
        PollPlantMonitoringData(plant_id=self.existent_plant.id)
        response = self.client.get('/plants/report/')
        data = response.json()
        datapoints = data['results'][0]['datapoints']
        self.assertEqual(
            datapoints,
            [
                {
                    'timestamp': '2019-01-01T01:00:00Z',
                    "energy_expected": 87.55317774223157,
                    "energy_observed": 90.78559770167864,
                    "irradiation_expected": 98.19878838432548,
                    "irradiation_observed": 30.085498370965905
                }
            ]
        )
