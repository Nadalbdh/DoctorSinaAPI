import json
import shutil
from unittest.mock import patch

from django.test import override_settings
from freezegun import freeze_time
from model_bakery import baker
from rest_framework import status
from rest_framework.renderers import JSONRenderer

from backend.functions import get_file_url
from backend.models import SubjectAccessRequest
from backend.serializers.serializers import SubjectAccessRequestSerializer
from backend.tests.test_base import (
    authenticate_citizen_test,
    ElBaladiyaAPITest,
    MunicipalityTestMixin,
    TestBase,
)
from backend.tests.test_utils import force_date_attribute
from notifications.models import Notification

TEST_DIR = "test_dir"


class SARViewTest(ElBaladiyaAPITest):
    url_name = "backend:subject-access-request"
    default_model = "backend.subjectaccessrequest"

    @override_settings(MEDIA_ROOT=(TEST_DIR + "/media"))
    @authenticate_citizen_test
    def test_delete_attachment(self):
        sar = self.make_with_municipality(
            created_by=self.citizen.user,
            _create_files=True,
            _fill_optional=["attachment"],
        )
        attachment = sar.attachment

        self.assertFileIsNotNone(attachment)

        # Send request to delete and delete the file
        response = self.client.put(
            self.get_url(sar.pk),
            {
                "attachment": None,
                "document": "very secret",
                "structure": "complete lattice",
            },
            format="json",
        )
        sar.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFileIsNone(sar.attachment)
        # Old file is deleted
        # self.assertFileNotExists(attachment) FIXME

    def test_get_public(self):
        # TODO also check response content
        response = self.client.get(self.get_url(), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @freeze_time("2020-11-20")
    @authenticate_citizen_test
    def test_get_filter_created_at_in_range(self):
        self.make_with_municipality(created_by=self.citizen.user, _quantity=3)

        sar_before_range = self.make_with_municipality(
            created_by=self.citizen.user, _quantity=4
        )

        for sar in sar_before_range:
            force_date_attribute(sar, "2019-01-04")

        sar_after_range = self.make_with_municipality(
            created_by=self.citizen.user, _quantity=4
        )

        for sar in sar_after_range:
            force_date_attribute(sar, "2025-01-04")

        response = self.client.get(
            self.get_url() + "?created_at__range=2020-09-01,2021-01-31", format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)

    @authenticate_citizen_test
    def test_create_sar(self):
        pdf = ""
        with open("test_resources/pdf_base64") as f:
            pdf = f.read()

        response = self.client.post(
            self.get_url(),
            {
                "document": "very secret",
                "structure": "complete lattice",
                "attachment": pdf,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @authenticate_citizen_test
    def test_delete_sar(self):
        sar = self.make_with_municipality(created_by=self.citizen.user)
        sar.refresh_from_db()
        response = self.client.delete(
            self.get_url(sar.pk),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEmpty(SubjectAccessRequest.objects.all())

    @authenticate_citizen_test
    def test_get_sar(self):
        sar = self.make_with_municipality(
            created_by=self.citizen.user,
        )
        sar.refresh_from_db()
        response = self.client.get(
            self.get_url(sar.pk),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @authenticate_citizen_test
    def test_update_sar(self):
        sar = self.make_with_municipality(created_by=self.citizen.user)
        response = self.client.post(
            "%s/update" % self.get_url(sar.pk),
            {"status": "ACCEPTED", "note": "This SAR is accepted"},
            format="json",
        )
        sar.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Notification.objects.all().first().municipality.id, sar.municipality.id
        )

    @classmethod
    def tearDownClass(cls):
        try:
            shutil.rmtree(TEST_DIR)
        except OSError:
            pass

        return super().tearDownClass()


class SARSerializerTest(MunicipalityTestMixin, TestBase):
    def test_serializer(self):
        citizen = baker.make("backend.citizen")

        sar = self.make_with_municipality(
            "backend.subjectaccessrequest",
            created_by=citizen.user,
            document="dostour",
            note="Fasl 80",
            is_public=True,
            reference="idk",
            printed_document=True,
            parts_of_document=True,
            _create_files=True,
            _fill_optional=["attachment"],
        )

        time_format = "%Y-%m-%dT%H:%M:%S.%fZ"

        expected = {
            "municipality": sar.municipality_id,
            "id": sar.id,
            "document": sar.document,
            "remarque": sar.note,
            "note": sar.note,
            "is_public": sar.is_public,
            "structure": sar.structure,
            "ref": sar.reference,
            "reference": sar.reference,
            "attachment": get_file_url(sar.attachment),
            "on_spot_document": sar.on_spot_document,
            "printed_document": sar.printed_document,
            "electronic_document": sar.electronic_document,
            "parts_of_document": sar.parts_of_document,
            "created_at": sar.created_at.strftime(time_format),
            "created_by_id": sar.created_by.id,
            "created_by": sar.created_by.id,
            "user_fullname": sar.created_by.get_full_name(),
            "user_email": sar.created_by.email,
            "followers": list(sar.followers.all().values_list("id", flat=True)),
            "user_phone": None,  # shhhh
            "user_address": sar.created_by.citizen.address,
            "updates": [
                {
                    "date": operation_update.created_at.strftime(time_format),
                    "status": operation_update.status,
                    "note": operation_update.note,
                    "id": sar.id,
                    "created_by": operation_update.created_by.id
                    if operation_update.created_by is not None
                    else None,
                    "created_by_name": operation_update.created_by.get_full_name()
                    if operation_update.created_by is not None
                    else None,
                    "image": None,
                }
                for operation_update in sar.operation_updates.all()
            ],
            "contested": False,
            "hits": sar.hits_count,
        }

        actual = json.loads(
            JSONRenderer().render(SubjectAccessRequestSerializer(sar).data)
        )

        self.assertEqual(actual, expected)
        self.assertDictEqual(actual, expected)
