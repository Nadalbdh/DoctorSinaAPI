from unittest.mock import patch

from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from backend.tests.test_base import (
    authenticate_citizen_test,
    authenticate_manager_test,
    cleanup_test_files,
    ElBaladiyaAPITest,
)


class ExportSARasDOCXTest(ElBaladiyaAPITest):
    view_name = "backend:export-sar-docx"

    @cleanup_test_files
    @authenticate_citizen_test
    @patch(
        "backend.views.export_to_docx.ExportSubjectAccessRequestToDocxView.get_document_buffer"
    )
    def test_export_sar_as_docx(self, mock):
        sar = baker.make("backend.subjectaccessrequest", created_by=self.citizen.user)
        response = self.client.get(
            reverse(
                self.view_name,
                args=[self.municipality.pk, sar.pk],
            ),
        )
        filename = f"access_request_to_numero_{sar.pk}"
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.as_attachment)
        self.assertEqual(response.filename, f"{filename}.docx")
        self.assertTrue(mock.called)

    @cleanup_test_files
    @authenticate_manager_test
    @patch(
        "backend.views.export_to_docx.ExportSubjectAccessRequestToDocxView.get_document_buffer"
    )
    def test_export_sar_as_docx_for_managers(self, mock):
        sar = baker.make(
            "backend.subjectaccessrequest",
            document="docdoc",
            id=55,
            created_by=self.citizen.user,
        )
        response = self.client.get(
            reverse(
                self.view_name,
                args=[self.municipality.pk, sar.pk],
            ),
        )
        filename = f"access_request_to_numero_{sar.pk}"
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.as_attachment)
        self.assertEqual(response.filename, f"{filename}.docx")
        self.assertTrue(mock.called)

    @cleanup_test_files
    @authenticate_citizen_test
    def test_export_sar_as_docx_not_authorized(self):
        sar = baker.make(
            "backend.subjectaccessrequest",
            document="docdoc",
            id=55,
            created_by=baker.make("backend.citizen").user,
        )
        response = self.client.get(
            reverse(
                self.view_name,
                args=[self.municipality.pk, sar.pk],
            ),
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
