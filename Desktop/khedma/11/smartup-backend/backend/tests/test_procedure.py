import json

from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from backend.models import Municipality, Procedure
from backend.tests.test_base import ElBaladiyaAPITest
from backend.tests.test_utils import check_equal_attributes
from factories import UserFactory


class ProcedureTest(ElBaladiyaAPITest):
    def setUp(self):
        self.client.force_authenticate(user=UserFactory())
        self.municipality = Municipality.objects.get(pk=1)
        Procedure.objects.create(
            title="Title", body="", municipality=self.municipality, display_order=1
        )

    def test_get_procedures(self):
        procedures = self.municipality.procedures.all()
        response = self.client.get(reverse("backend:procedures", args=[1]))
        response_obj = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_obj), len(procedures))

    def test_get_procedure(self):
        procedure = self.municipality.procedures.last()
        url = reverse("backend:procedure", args=[1, procedure.pk])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            check_equal_attributes(
                procedure, response.data, ["body", "title", "municipality_id"]
            )
        )

    def test_create_procedure(self):  # TODO remove attributes, check
        self.make_manager()
        data = {
            "municipality_id": 1,
            "title": "POST_CORRECT",
            "body": "POST_CORRECT_BODY",
            "display_order": 0,
        }

        url = reverse("backend:procedures", args=[1])
        response = self.client.post(url, data)
        procedure = Procedure.objects.last()
        # Status
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # check returned object against db object
        self.assertTrue(
            check_equal_attributes(
                procedure, response.data, ["body", "title", "municipality_id"]
            )
        )
        # check db object against initial object
        self.assertTrue(
            check_equal_attributes(
                procedure,
                data,
                ["body", "title", "municipality_id", "display_order"],
            )
        )

    def test_update_procedure(self):
        self.make_manager()
        Procedure.objects.create(
            municipality_id=1,
            title="TEST_UPDATE",
            body="THIS IS AN UPDATE TEST",
            display_order=3,
        )
        procedure = Procedure.objects.last()
        old_object = procedure.to_dict()
        data = {"body": "CHANGED"}
        url = reverse("backend:procedure", args=[1, 2])
        old_object[
            "display_order"
        ] = procedure.display_order  # Not returned from to_dict()
        response = self.client.put(url, data)
        procedure.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # only specified attributes changed
        self.assertTrue(
            check_equal_attributes(
                procedure, old_object, ["title", "display_order", "municipality_id"]
            )
        )
        # check if the returned object matches the db object
        self.assertTrue(
            check_equal_attributes(
                procedure, response.data, ["body", "title", "municipality_id"]
            )
        )
        # check that the new value is inserted
        self.assertEqual("CHANGED", response.data["body"])

    def test_delete_citizen_procedure(self):
        previous_length = self.municipality.procedures.all().count()
        url = reverse("backend:procedure", args=[1, 2])
        response = self.client.delete(url, response_json=False)

        self.municipality.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(previous_length, self.municipality.procedures.all().count())

    def test_delete_manager_procedure(self):
        self.make_manager()
        # get last object in the database
        procedure = Procedure(
            municipality_id=1,
            title="TEST_Create",
            body="THIS IS A Create TEST",
            display_order=3,
        )
        procedure.save()

        url = reverse("backend:procedure", args=[1, procedure.pk])
        response = self.client.delete(url, response_json=False)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Procedure.objects.filter(pk=procedure.pk).exists())

    def test_not_found(self):
        url = reverse("backend:procedure", args=[self.municipality.id, 420])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def make_manager(self):
        # set up manager rights
        manager = baker.make("backend.manager", municipality=self.municipality)
        self.client.force_authenticate(user=manager.user)
