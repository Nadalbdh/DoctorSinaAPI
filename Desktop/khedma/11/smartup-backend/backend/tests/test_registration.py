from datetime import datetime
from unittest.mock import patch

import jwt
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.views import TokenVerifyView

from backend.registration_otp_manager import MAX_OTP_RETRIES
from sms.enum import SMSQueueStatus

from .test_base import ElBaladiyaAPITest
from .test_utils import fake, get_random_municipality_id, get_random_phone_number


class RegistrationTest(ElBaladiyaAPITest):
    # Don't actually call the API, just mock it
    @patch("utils.SMSManager.SMSManager.send_sms", return_value=SMSQueueStatus.SENT)
    def test_registration(self, mock):
        # SMSManager logs

        registration_url = reverse("backend:register")
        phone_number = get_random_phone_number()
        data = {
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "phone_number": phone_number,
            "password": fake.word(),
            "birth_date": fake.date(),
            "municipality_id": self.municipality.id,
        }
        response = self.client.post(registration_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        verify_otp_data = {
            "phone_number": phone_number,
            "otp": _extract_otp_from_mocked_sms(mock),
        }
        verify_otp_url = reverse("backend:verify_otp")
        response = self.client.post(verify_otp_url, verify_otp_data)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        new_user = User.objects.get(username=phone_number)
        self.assertTrue(new_user.is_active)
        self.assertTrue(hasattr(new_user, "citizen"))
        self.assertEqual(new_user.citizen.registration_municipality, self.municipality)
        self.assertEqual(new_user.citizen.preferred_municipality, self.municipality)
        self.assertIn(self.municipality, new_user.citizen.municipalities.all())
        self.assertIn(new_user.citizen, self.municipality.citizens.all())
        self.assertFalse(new_user.citizen.is_deleted)

    # Don't actually call the API, just mock it
    @patch("utils.SMSManager.SMSManager.send_sms", return_value=0)
    def test_block_sms_after_max_requests(self, mock):
        # SMSManager logs
        url = reverse("backend:register")
        data = {
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "phone_number": get_random_phone_number(),
            "password": fake.word(),
            "birth_date": fake.date(),
            "municipality_id": get_random_municipality_id(),
        }
        for _ in range(MAX_OTP_RETRIES):
            self.client.post(url, data)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class ResetPasswordTest(ElBaladiyaAPITest):
    @patch("utils.SMSManager.SMSManager.send_sms", return_value=SMSQueueStatus.SENT)
    def test_reset_password_citizen(self, mock):
        url = reverse("backend:reset_password")
        phone_number = get_random_phone_number()
        self.citizen.user.username = phone_number
        self.citizen.user.is_active = False
        self.citizen.user.save()
        data = {"type": "SMS", "phone_number": phone_number}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        reset_password_verify_url = reverse("backend:reset_password_verify")
        reset_password_verify_data = {
            "phone_number": phone_number,
            "otp": _extract_otp_from_mocked_sms(mock),
        }
        response = self.client.post(
            reset_password_verify_url, reset_password_verify_data
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        new_jwt_token = response.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {new_jwt_token}")
        # try using the new jwt to fetch new data
        self.assertEqual(
            self.client.get(reverse("backend:profile")).status_code, status.HTTP_200_OK
        )
        self.assertTrue(User.objects.get(username=phone_number).is_active)

    @patch("utils.SMSManager.SMSManager.send_sms", return_value=SMSQueueStatus.SENT)
    def test_reset_password_manager(self, mock):
        url = reverse("backend:manager_reset_password")
        phone_number = get_random_phone_number()
        self.manager.user.username = f"M{phone_number}"
        self.manager.user.is_active = False
        self.manager.user.save()
        data = {"type": "SMS", "phone_number": phone_number}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        reset_password_verify_url = reverse("backend:manager_reset_password_verify")
        reset_password_verify_data = {
            "phone_number": phone_number,
            "otp": _extract_otp_from_mocked_sms(mock),
        }
        response = self.client.post(
            reset_password_verify_url, reset_password_verify_data
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        decoded_new_jwt = jwt.decode(response.json()["access"], None, None)
        self.assertGreater(decoded_new_jwt["exp"], datetime.now().timestamp())


def _extract_otp_from_mocked_sms(mock):
    return mock.call_args_list[0][0][1][:6]
