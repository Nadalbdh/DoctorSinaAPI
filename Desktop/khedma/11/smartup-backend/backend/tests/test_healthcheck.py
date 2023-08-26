from unittest.mock import patch

from django.urls import reverse
from model_bakery import baker
from rest_framework.status import HTTP_200_OK, HTTP_500_INTERNAL_SERVER_ERROR

from backend.tests.test_base import ElBaladiyaAPITest


class HealthCheckTest(ElBaladiyaAPITest):
    def setUp(self):
        super().setUp()
        baker.make(
            "etickets_v2.Agency",
            municipality=self.municipality,
            is_active=True,
            _quantity=10,
        )

    @patch("backend.functions.server_works")
    def test_local_server_are_working(self, mock):
        baker.make(
            "etickets_v2.Agency",
            is_active=True,
            name="dev-server",
            municipality=self.municipality,
            local_ip="dev-backend.elbaladiya.tn",
        )
        mock.return_value.returncode = 0
        response = self.client.get(reverse("backend:health"))
        self.assertEqual(response.data.__len__(), 11)
        self.assertFalse(mock.called)
        self.assertTrue(response.data[10]["is_up"])
        self.assertTrue(response.status_code, HTTP_500_INTERNAL_SERVER_ERROR)
