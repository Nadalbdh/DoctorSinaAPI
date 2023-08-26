from unittest.mock import patch

from django.core.cache import cache
from django.urls import reverse
from guardian.shortcuts import assign_perm
from model_bakery import baker
from rest_framework import status

from backend.enum import MunicipalityPermissions
from backend.helpers import ManagerHelpers
from backend.tests.test_base import (
    authenticate_citizen_test,
    authenticate_manager_test,
    ElBaladiyaAPITest,
)
from notifications.models import Notification


class OperationUpdateTest(ElBaladiyaAPITest):
    def setUp(self):
        super().setUp()
        self.citizen = baker.make("backend.citizen")
        self.manager = baker.make("backend.manager", municipality=self.municipality)

    def update_model(self, viewname: str, payload, args, suffix="/update"):
        return self.client.post(
            reverse(
                viewname,
                args=args,
            )
            + suffix,
            payload,
        )

    def assert_has_operation_image(self, response):
        self.assertTrue(
            response.data["updates"][0]["image"].startswith("/media/operation-updates/")
        )
        self.assertTrue(response.data["updates"][0]["image"].endswith(".png"))

    @authenticate_manager_test
    def test_get_operation_updates(self):
        operation_update = baker.make("backend.OperationUpdate", id=100)
        response = self.client.get(
            reverse(
                "backend:operation-update",
                args=[self.manager.municipality.pk, operation_update.pk],
            )
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    @authenticate_manager_test
    def test_delete_operation_updates(self):
        operation_update = baker.make("backend.OperationUpdate", id=100)
        response = self.client.delete(
            reverse(
                "backend:operation-update",
                args=[self.manager.municipality.pk, operation_update.pk],
            )
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    @authenticate_manager_test
    def test_post_operation_updates(self):
        operation_update = baker.make("backend.OperationUpdate", id=100)
        data = {"image": "data:image/png;base64,R0lGODlhAQABAAAAACw="}
        response = self.client.post(
            reverse(
                "backend:operation-update",
                args=[self.manager.municipality.pk, operation_update.pk],
            ),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    @authenticate_manager_test
    def test_put_operation_updates(self):
        operation_update = baker.make("backend.OperationUpdate", id=100)
        data = {"image": "data:image/png;base64,R0lGODlhAQABAAAAACw="}
        response = self.client.put(
            reverse(
                "backend:operation-update",
                args=[self.manager.municipality.pk, operation_update.pk],
            ),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["image"].startswith("/media/operation-updates/"))
        self.assertTrue(response.data["image"].endswith(".png"))

    @authenticate_manager_test
    def test_put_operation_update_img_to_null(self):
        operation_update = baker.make(
            "backend.OperationUpdate",
            id=100,
            image="data:image/png;base64,R0lGODlhAQABAAAAACw=",
        )
        data = {"image": None}
        response = self.client.put(
            reverse(
                "backend:operation-update",
                args=[self.manager.municipality.pk, operation_update.pk],
            ),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        operation_update.refresh_from_db()
        self.assertFileIsNone(operation_update.image)

    @authenticate_citizen_test
    def test_put_operation_updates_without_perm(self):
        operation_update = baker.make("backend.OperationUpdate", id=100)
        data = {"image": "data:image/png;base64,R0lGODlhAQABAAAAACw="}
        response = self.client.put(
            reverse(
                "backend:operation-update",
                args=[self.manager.municipality.pk, operation_update.pk],
            ),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate_manager_test
    def test_get_object_with_updates_image(self):
        operation_update = baker.make("backend.OperationUpdate", id=55)
        baker.make(
            "backend.complaint",
            municipality=self.manager.municipality,
            operation_updates=[operation_update],
            id=100,
        )
        data = {"image": "data:image/png;base64,R0lGODlhAQABAAAAACw="}
        response = self.client.get(
            reverse(
                "backend:complaint",
                args=[self.municipality.pk, 100],
            ),
        )
        self.assertIsNone(response.data["updates"][0]["image"])
        put_response = self.client.put(
            reverse(
                "backend:operation-update",
                args=[self.manager.municipality.pk, operation_update.pk],
            ),
            data,
            format="json",
        )
        self.assertEqual(put_response.status_code, 200)
        cache.clear()
        response = self.client.get(
            reverse(
                "backend:complaint",
                args=[self.municipality.pk, 100],
            ),
        )
        self.assert_has_operation_image(response)

    def test_get_operation_update_with_ids(self):
        """assert that an Updateble object operation has an id"""
        operation_update = baker.make("backend.OperationUpdate")
        complaint = baker.make(
            "backend.complaint",
            municipality=self.manager.municipality,
            operation_updates=[operation_update],
        )
        response = self.client.get(
            reverse(
                "backend:complaint",
                args=[self.municipality.pk, complaint.pk],
            ),
        )
        self.assertEqual(response.data["updates"][0]["id"], operation_update.pk)

    @authenticate_manager_test
    def test_post_comment_with_updates_image(self):
        assign_perm(
            MunicipalityPermissions.MANAGE_COMPLAINTS,
            self.manager.user,
            self.municipality,
        )
        comment = baker.make(
            "backend.comment",
            municipality=self.manager.municipality,
            created_by=self.manager.user,
            body="body content",
        )
        data = {
            "status": "ACCEPTED",
            "id": comment.pk,
            "note": "all good mr citizen, and this is an image to prove it",
            "image": "data:image/png;base64,R0lGODlhAQABAAAAACw=",
        }

        response = self.update_model(
            "backend:comment-status",
            data,
            [
                self.municipality.pk,
                comment.pk,
            ],
            "",
        )

        self.assertEqual(response.status_code, 200)
        self.assert_has_operation_image(response)
        self.assertEqual(
            Notification.objects.all().first().municipality.id, comment.municipality.id
        )

    @authenticate_manager_test
    def test_post_comment_without_updates_image(self):
        assign_perm(
            MunicipalityPermissions.MANAGE_COMPLAINTS,
            self.manager.user,
            self.municipality,
        )
        comment = baker.make(
            "backend.comment",
            municipality=self.manager.municipality,
            created_by=self.manager.user,
            body="body content",
        )
        data = {
            "status": "ACCEPTED",
            "id": comment.pk,
            "note": "all good mr citizen, and this is an image to prove it",
        }

        response = self.update_model(
            "backend:comment-status",
            data,
            [
                self.municipality.pk,
                comment.pk,
            ],
            "",
        )

        self.assertEqual(response.status_code, 200)

    @authenticate_manager_test
    def test_post_complaint_with_updates_image(self):
        food = baker.make("backend.complaintcategory", name="food")
        drinks = baker.make("backend.complaintcategory", name="drinks")
        complaint = self.make_with_municipality("backend.complaint", category=food)

        self.manager.complaint_categories.set([food, drinks])
        data = {
            "image": "data:image/png;base64,R0lGODlhAQABAAAAACw=",
            "category": "string",
            "region": "string",
            "sub_category": "string",
            "created_by_id": self.manager.user.pk,
            "longitude": "string",
            "latitude": "string",
            "address": "string",
            "problem": "string",
            "solution": "string",
            "is_public": True,
            "status": "ACCEPTED",
            "municipality": self.municipality.pk,
        }

        response = self.update_model(
            "backend:complaint",
            data,
            [
                self.municipality.pk,
                complaint.pk,
            ],
        )

        self.assertEqual(response.status_code, 200)
        self.assert_has_operation_image(response)
        self.assertEqual(
            Notification.objects.all().first().municipality.id,
            complaint.municipality.id,
        )

    @authenticate_manager_test
    def test_post_dossier_with_updates_image(self):
        self.assertEqual(Notification.objects.all().count(), 0)
        dossier = self.make_with_municipality(
            "backend.Dossier", created_by=self.citizen.user
        )
        data = {"note": "mmm", "status": "PROCESSING"}
        ManagerHelpers(self.manager, self.municipality).assign_permissions(
            [MunicipalityPermissions.MANAGE_DOSSIERS]
        )
        data = {
            "created_by_id": self.manager.user.pk,
            "phone_number": "string",
            "name": "string",
            "type": "BUILDING",
            "unique_identifier": "string",
            "cin_number": "string",
            "deposit_date": "2022-11-29",
            "image": "data:image/png;base64,R0lGODlhAQABAAAAACw=",
            "status": "ACCEPTED",
            "municipality": self.municipality.pk,
        }
        response = self.update_model(
            "backend:dossier",
            data,
            [
                self.municipality.pk,
                dossier.pk,
            ],
        )

        self.assertEqual(response.status_code, 200)
        self.assert_has_operation_image(response)

    @authenticate_manager_test
    def test_post_subject_access_requests_with_updates_image(self):
        subjectaccessrequest = self.make_with_municipality(
            "backend.subjectaccessrequest",
            created_by=baker.make("backend.citizen").user,
        )
        data = {
            "created_by_id": baker.make("backend.citizen").user,
            "attachment": "string",
            "image": "data:image/png;base64,R0lGODlhAQABAAAAACw=",
            "document": "string",
            "is_public": True,
            "structure": "string",
            "reference": "string",
            "on_spot_document": True,
            "printed_document": True,
            "electronic_document": True,
            "parts_of_document": True,
            "contested": True,
            "note": "string",
            "status": "ACCEPTED",
            "municipality": self.municipality.pk,
        }

        response = self.update_model(
            "backend:subject-access-request",
            data,
            [self.municipality.pk, subjectaccessrequest.pk],
        )

        self.assertEqual(response.status_code, 200)
        self.assert_has_operation_image(response)
