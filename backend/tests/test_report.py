import datetime
import random
from http import HTTPStatus

import pytz
from django.conf import settings
from django.test import TestCase
from schema import Schema, Or

from backend.models import Plant, Datapoint

REPORT_SCHEMA = Schema({
    'count': int,
    'next': Or(str, None),
    'previous': Or(str, None),
    'results': [{
        'id': int,
        'name': str,
        'datapoints': [{
            'timestamp': str,
            'energy_expected': float,
            'energy_observed': float,
            'irradiation_expected': float,
            'irradiation_observed': float,
        }]
    }]
})


class ReportTestCase(TestCase):
    def setUp(self):
        self.existent_plant = Plant.objects.create(
            name='existent-plant'
        )

        datapoints = []
        time_zone = pytz.timezone(settings.TIME_ZONE)
        timestamp = datetime.datetime(2020, 1, 1, tzinfo=time_zone)
        while timestamp < datetime.datetime(2021, 1, 1, tzinfo=time_zone):
            datapoints.append(Datapoint(
                plant=self.existent_plant,
                timestamp=timestamp,
                energy_expected=random.random() * 100,
                energy_observed=random.random() * 100,
                irradiation_expected=random.random() * 100,
                irradiation_observed=random.random() * 100,
            ))
            timestamp += datetime.timedelta(hours=1)

        Datapoint.objects.bulk_create(datapoints)

    def test_report(self):
        """A report is correctly produced without any filtering parameters"""
        response = self.client.get('/plants/report/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(REPORT_SCHEMA.is_valid(response.json()))

    def test_plant_report(self):
        """A report is correctly produced for a given plant"""
        response = self.client.get(
            '/plants/report/',
            data={
                'plant_ids': [self.existent_plant.id]
            }
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(len(data['results']), 1)

    def test_invalid_plant_report(self):
        """A report fails to generate for invalid plants"""
        response = self.client.get(
            '/plants/report/',
            data={
                'plant_ids': [self.existent_plant.id, 2]
            }
        )
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_from_date_report(self):
        """A report is correctly produced for a given starting date"""
        response = self.client.get(
            '/plants/report/',
            data={
                'from': '2020-12-01'
            }
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(
            len(data['results'][0]['datapoints']),
            31 * 24  # 31 days
        )

    def test_to_date_report(self):
        """A report is correctly produced for a given ending date"""
        response = self.client.get(
            '/plants/report/',
            data={
                'to': '2020-01-31'
            }
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(
            len(data['results'][0]['datapoints']),
            30 * 24  # 30 days ('to' date is excluded)
        )

    def test_date_range_report(self):
        """A report is correctly produced for a given date range"""
        response = self.client.get(
            '/plants/report/',
            data={
                'from': '2020-05-01',
                'to': '2020-05-31',
            }
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(
            len(data['results'][0]['datapoints']),
            30 * 24  # 30 days ('to' date is excluded)
        )

    def test_invalid_dates_report(self):
        """A report fails to generate for invalid date filters"""
        response = self.client.get(
            '/plants/report/',
            data={
                'from': '2020-02-30',  # invalid date
            }
        )
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
