from datetime import datetime

from django.urls import reverse
from freezegun import freeze_time
from model_bakery import baker
from rest_framework import status

from backend.models import RegisteredDevice
from backend.tests.test_base import ElBaladiyaAPITest


class LoginAPITest(ElBaladiyaAPITest):
    def test_citizen_deprecated_username(self):
        response = self.client.post(
            reverse("backend:login"),
            {
                "username": self.citizen.to_dict()["phone_number"],
                "password": "incorrect_pwd",
            },
            format="json",
        )
        assert response.status_code == 400
        assert (
            response.json()["details"]
            == "Attribute: 'username' is no longer used, Please remove it and use 'phone_number' instead"
        )

    @freeze_time("2021-01-12")
    def test_citizen_jwt_login(self):
        self.citizen = baker.make(
            "backend.citizen",
            user__username="22449506",
            user__is_active=True,
            municipalities=[self.municipality],
        )
        self.citizen.user.set_password("test_password")
        self.citizen.user.save()
        response = self.client.post(
            reverse("backend:login"),
            {
                "phone_number": self.citizen.to_dict()["phone_number"],
                "password": "incorrect_pwd",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.post(
            reverse("backend:login"),
            {
                "phone_number": self.citizen.to_dict()["phone_number"],
                "password": "test_password",
                "device_unique_id": "mydeviceuniqueid",
            },
            format="json",
        )
        device = RegisteredDevice.objects.filter(device_unique_id="mydeviceuniqueid")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(device.exists())
        self.assertTrue(response.data["first_login"])
        self.assertEqual(
            response.data["latest_residence_update_date"],
            datetime.strptime("2021-01-12", "%Y-%m-%d").date(),
        )
        self.assertEqual(
            response.data["preferred_municipality_id"],
            self.citizen.to_dict()["preferred_municipality_id"],
        )
        self.assertTrue(response.data["is_active"])
