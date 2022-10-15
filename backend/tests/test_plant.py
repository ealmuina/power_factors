from http import HTTPStatus

from django.test import TestCase

from backend.models import Plant


class PlantTestCase(TestCase):
    def setUp(self):
        self.existent_plant = Plant.objects.create(
            name='existent-plant'
        )

    def test_create_plant(self):
        """A valid new plant is created correctly"""
        plant_name = 'new-plant'
        response = self.client.post(
            path='/plants/',
            data={
                'name': plant_name
            }
        )
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertTrue(
            Plant.objects.filter(name=plant_name).exists()
        )

    def test_create_duplicated_plant(self):
        """Creating a plant with a duplicated name fails"""
        response = self.client.post(
            path='/plants/',
            data={
                'name': self.existent_plant.name
            }
        )
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_list_plants(self):
        """Plants are listed correctly"""
        response = self.client.get('/plants/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(
            dict(results[0]),
            {
                'id': self.existent_plant.id,
                'name': self.existent_plant.name
            }
        )

    def test_read_plant(self):
        """A plant details are read correctly"""
        response = self.client.get(f'/plants/{self.existent_plant.id}/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            response.data,
            {
                'id': self.existent_plant.id,
                'name': self.existent_plant.name
            }
        )

    def test_update_plant(self):
        """A plant is updated correctly"""
        updated_name = f"{self.existent_plant.name}-updated"
        response = self.client.patch(
            path=f'/plants/{self.existent_plant.id}/',
            data={
                'name': updated_name
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(
            Plant.objects.filter(name=self.existent_plant.name).exists()
        )
        self.assertTrue(
            Plant.objects.filter(name=updated_name).exists()
        )

    def test_update_nonexistent_plant(self):
        """A nonexistent plant fails to update"""
        updated_name = 'nonexistent-plant'
        response = self.client.patch(
            path='/plants/2/',
            data={
                'name': updated_name
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertFalse(
            Plant.objects.filter(name=updated_name).exists()
        )

    def test_update_duplicates_plant(self):
        """Updating a plant to a duplicate name fails"""
        new_plant = Plant.objects.create(name='plant-2')
        response = self.client.patch(
            path=f'/plants/{new_plant.id}/',
            data={
                'name': self.existent_plant.name
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_delete_plant(self):
        """A plant is deleted correctly"""
        response = self.client.delete(f'/plants/{self.existent_plant.id}/')
        self.assertEqual(response.status_code, HTTPStatus.NO_CONTENT)
        self.assertEqual(Plant.objects.count(), 0)

    def test_delete_nonexistent_plant(self):
        """A nonexistent plant fails to delete"""
        response = self.client.delete(f'/plants/2/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
