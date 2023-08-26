from django.test import RequestFactory
from django.urls import reverse

from api_logger.utils import get_client_ip, mask_sensitive_data
from backend.tests.test_base import ElBaladiyaAPITest


class APILogUtilsTest(ElBaladiyaAPITest):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()

    def test_get_client_ip(self):
        test_ip_address = "200.1.23.3"
        request = self.factory.get(
            reverse("backend:municipalities"), HTTP_X_FORWARDED_FOR=test_ip_address
        )
        ip = get_client_ip(request)
        self.assertEqual(ip, test_ip_address)

    def test_hide_sensitive_data(self):
        data = {
            "user": {
                "username": "test_user",
                "password": "very_secure_pass",
                "cin": "00896315",
                "image": "some_long_base64_string",
            },
            "body": "some_random_content",
            "token": "some_token",
            "access": "some_access",
            "refresh": "some_refresh",
            "file": "some_long_base64_string",
            "attachment": "some_long_base64_string",
        }
        expected_ouput = {
            "user": {
                "username": "test_user",
                "password": "***HIDDEN***",
                "cin": "***HIDDEN***",
                "image": "***HIDDEN***",
            },
            "body": "some_random_content",
            "token": "***HIDDEN***",
            "access": "***HIDDEN***",
            "refresh": "***HIDDEN***",
            "file": "***HIDDEN***",
            "attachment": "***HIDDEN***",
        }
        self.assertEqual(mask_sensitive_data(data), expected_ouput)
