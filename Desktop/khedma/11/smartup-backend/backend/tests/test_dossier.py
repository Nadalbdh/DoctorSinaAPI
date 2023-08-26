from datetime import date
from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from backend.enum import MunicipalityPermissions
from backend.helpers import get_unique_identifier, ManagerHelpers
from backend.models import Dossier
from backend.tests.test_base import (
    authenticate_citizen_test,
    authenticate_manager_test,
    ElBaladiyaAPITest,
)


class DossierViewTest(ElBaladiyaAPITest):
    url_name = "backend:dossier"

    @authenticate_citizen_test
    def test_update_phone_number(self):
        dossier = baker.make(
            "backend.dossier",
            created_by=self.citizen.user,
            municipality=self.municipality,
            _fill_optional=["phone_number"],
        )

        self.assertIsNotNone(dossier.phone_number)

        new_phone_number = "97393123"
        response = self.client.put(
            self.get_url(dossier.pk), {"phone_number": new_phone_number}, format="json"
        )
        dossier.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(new_phone_number, dossier.phone_number)

    @authenticate_citizen_test
    def test_create_dossier_by_citizen(self):
        data = {
            "title": "hhh",
            "name": "okok",
            "unique_identifier": "464",
            "cin_number": "74764",
            "note": "",
            "deposit_date": "2020-01-30",
        }
        response = self.client.post(self.get_url(), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get("created_by_id"), self.citizen.user.pk)

    @authenticate_citizen_test
    def test_create_dossier_with_random_unique_identifier(self):
        data = {
            "title": "hhh",
            "name": "okok",
            "cin_number": "74764",
            "note": "",
            "deposit_date": "2020-01-30",
        }
        response = self.client.post(self.get_url(), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get("created_by_id"), self.citizen.user.pk)
        self.assertTrue(len(response.data.get("unique_identifier")) > 3)

    @authenticate_citizen_test
    @patch("random.randint", side_effect=[10, 10, 10, 50])
    def test_get_unique_identifier_method(self, mocked_response):
        unique_identifier = get_unique_identifier(Dossier)
        self.assertEqual(unique_identifier, 10)
        data = {
            "title": "hhh",
            "name": "okok",
            "unique_identifier": "10",
            "cin_number": "74764",
            "note": "",
            "deposit_date": "2020-01-30",
        }
        response = self.client.post(self.get_url(), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        unique_identifier = get_unique_identifier(Dossier)
        self.assertEqual(unique_identifier, 50)

    @authenticate_manager_test
    def test_create_dossier_by_manager(self):
        data = {
            "title": "hhh",
            "name": "okok",
            "unique_identifier": "464",
            "cin_number": "74764",
            "note": "",
            "deposit_date": "2020-01-30",
        }
        response = self.client.post(self.get_url(), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get("created_by_id"), self.manager.user.pk)

    @authenticate_citizen_test
    def test_update_dossier_citizen(self):
        dossier = self.make_with_municipality(
            "backend.Dossier", created_by=self.citizen.user
        )
        data = {"created_by": self.manager.user.pk}  # Created by cannot be updated
        response = self.client.put(self.get_url(dossier.pk), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("created_by_id"), self.citizen.user.pk)

    @authenticate_citizen_test
    def test_update_dossier_citizen_forbidden(self):
        """
        Citizen can only update  their dossier
        """
        dossier = self.make_with_municipality(
            "backend.Dossier", created_by=baker.make("backend.citizen").user
        )
        dossier.followers.add(self.citizen.user)
        data = {"name": "doc name"}  # Created by cannot be updated
        response = self.client.put(self.get_url(dossier.pk), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate_manager_test
    def test_update_dossier_manager_forbidden(self):
        """
        Manager can't update dossier (only status)
        """
        dossier = self.make_with_municipality(
            "backend.Dossier", created_by=baker.make("backend.citizen").user
        )
        data = {"name": "doc name"}  # Created by cannot be updated
        response = self.client.put(self.get_url(dossier.pk), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate_manager_test
    def test_delete_dossier_manager_forbidden(self):
        """
        Manager can't update dossier (only status)
        """
        dossier = self.make_with_municipality(
            "backend.Dossier", created_by=baker.make("backend.citizen").user
        )
        response = self.client.delete(self.get_url(dossier.pk), format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate_manager_test
    def test_status_update_dossier(self):
        dossier = self.make_with_municipality(
            "backend.Dossier", created_by=baker.make("backend.citizen").user
        )
        data = {"note": "mmm", "status": "PROCESSING"}
        ManagerHelpers(self.manager, self.municipality).assign_permissions(
            [MunicipalityPermissions.MANAGE_DOSSIERS]
        )
        response = self.client.post(
            self.get_url(dossier.pk) + "/update", data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data.get("updates")[0].get("status"), data.get("status")
        )

    @authenticate_citizen_test
    def test_duplicate_dossier_citizen(self):
        self.make_with_municipality(
            "backend.Dossier", created_by=self.citizen.user, unique_identifier="123"
        )
        data = {
            "title": "hhh",
            "name": "okok",
            "unique_identifier": "123",
            "cin_number": "74764",
            "note": "",
            "deposit_date": "2020-01-30",
        }
        response = self.client.post(self.get_url(), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data.get("details"),
            "UNIQUE constraint failed: backend_dossier.unique_identifier, "
            "backend_dossier.municipality_id",
        )


class DossierModelTest(ElBaladiyaAPITest):
    def test_no_contact_number(self):
        dossier = baker.make("backend.dossier", municipality=self.municipality)
        self.assertEmpty(dossier.contact_number)

    def test_contact_number_no_subscribers(self):
        dossier = baker.make(
            "backend.dossier",
            municipality=self.municipality,
            phone_number="98123456",
        )
        self.assertCountEqual(dossier.contact_number, [dossier.phone_number])

    def test_contact_number_subscriber(self):
        dossier = baker.make(
            "backend.dossier",
            municipality=self.municipality,
            phone_number="98123456",
        )
        user = baker.make(User, username="27123456")
        dossier.followers.add(user)
        self.assertCountEqual(dossier.contact_number, ["27123456", "98123456"])

    def test_contact_number_subscriber_owner(self):
        dossier = baker.make(
            "backend.dossier",
            municipality=self.municipality,
            phone_number="98123456",
        )
        user = baker.make(User, username="98123456")
        dossier.followers.add(user)
        self.assertCountEqual(dossier.contact_number, [dossier.phone_number])

    def test_no_number_subscriber(self):
        dossier = baker.make("backend.dossier", municipality=self.municipality)
        follower_phone = "67548932"
        follower = baker.make(User, username=follower_phone)
        dossier.followers.add(follower)
        self.assertCountEqual(dossier.contact_number, [follower_phone])

    def test_dossier_creation(self):
        data = {
            "cin_number": "321",
            "deposit_date": "2022-09-25",
            "name": "abcdef",
            "phone_number": "55778990",
            "status": "RECEIVED",
            "type": "SONEDE",
            "unique_identifier": "ABCDEFG",
        }
        url = reverse("backend:dossiers", args=[self.municipality.id])
        self.client.force_authenticate(user=self.manager.user)
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        dossier = Dossier.objects.get(unique_identifier=data["unique_identifier"])
        self.assertEqual(dossier.cin_number, data["cin_number"])
        self.assertEqual(dossier.deposit_date, date(2022, 9, 25))
        self.assertEqual(dossier.phone_number, data["phone_number"])
        self.assertEqual(dossier.status, data["status"])
        self.assertEqual(dossier.type, data["type"])
        self.assertEqual(dossier.unique_identifier, data["unique_identifier"])
        self.assertEqual(dossier.created_by, self.manager.user)
        self.assertEqual(dossier.operation_updates.last().created_by, self.manager.user)
