from model_bakery import baker
from rest_framework import status

from backend.models import Municipality
from backend.tests.test_base import (
    authenticate_citizen_test,
    authenticate_manager_test,
    ElBaladiyaAPITest,
    TestBase,
)
from backend.tests.test_utils import get_random_municipality_id


class BuildingViewTest(ElBaladiyaAPITest):
    url_name = "backend:building"

    def setUp(self):
        super().setUp()
        self.data = {
            "address": "string",
            "latitude": 10.231,
            "longitude": 10.231,
            "permit_reference": "string",
            "dossier": 1,
        }

    @authenticate_citizen_test
    def test_create_building_for_existing_dossier_by_citizen(self):
        self.create_dossier(created_by=self.citizen.user)
        response = self.client.post(self.get_url(), self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @authenticate_citizen_test
    def test_create_building_for_existing_dossier_another_citizen(self):
        self.create_dossier(created_by=baker.make("backend.citizen").user)
        response = self.client.post(self.get_url(), self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate_citizen_test
    def test_reference_many_buildings_for_existing_dossier(self):
        self.create_dossier(created_by=self.citizen.user)
        response = self.client.post(self.get_url(), self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(self.get_url(), self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @authenticate_manager_test
    def test_update_building_of_another_citizen_by_manager(self):
        dossier = self.create_dossier(created_by=baker.make("backend.citizen").user)
        building = self.create_building(dossier=dossier)
        response = self.client.put(self.get_url(building.pk), self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def create_dossier(self, **kwargs):
        return self.make_with_municipality("backend.Dossier", **kwargs)

    def create_building(self, **kwargs):
        return baker.make("backend.Building", **kwargs)
