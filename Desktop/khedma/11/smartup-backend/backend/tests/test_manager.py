from unittest.mock import patch

from django.core.cache import cache
from django.urls import reverse
from guardian.shortcuts import assign_perm
from model_bakery import baker
from rest_framework import status

from backend.enum import (
    CachePrefixes,
    MunicipalityPermissions,
    OsTypes,
    ResetPasswordTypes,
)
from backend.helpers import ManagerHelpers
from backend.models import Manager, RegisteredDevice
from backend.reset_password import prepare_reset_password_otp
from backend.tests.test_base import authenticate_manager_test, ElBaladiyaAPITest


class TestManager(ElBaladiyaAPITest):
    url_name = "backend:manager"
    default_model = "backend.manager"

    def test_citizen_login_as_manager(self):
        self.citizen = baker.make(
            "backend.citizen",
            user__username="M22222222",
            user__is_active=True,
            municipalities=[self.municipality],
        )
        self.citizen.user.set_password("password")
        self.citizen.user.save()
        response = self.client.post(
            reverse("backend:manager_login"),
            {"phone_number": self.citizen.user.username[1:], "password": "password"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], "Token is invalid or expired")

    def test_manager_login_without_device_data(self):
        """
        assert login can be successful without providing any device data
        """
        self.manager = baker.make(
            "backend.manager",
            user__username="M33333333",
            user__is_active=True,
            municipality=self.municipality,
        )
        self.manager.user.set_password("password")
        self.manager.user.save()
        response = self.client.post(
            reverse("backend:manager_login"),
            {"phone_number": self.manager.user.username[1:], "password": "password"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("municipality_id", response.data)
        self.assertEqual(response.data["municipality_id"], self.manager.municipality.pk)

    def test_manager_login_with_device_data(self):
        """
        assert device data is being stored if it's provided
        """
        self.manager = baker.make(
            "backend.manager",
            user__username="M33333333",
            user__is_active=True,
            municipality=self.municipality,
        )
        self.manager.user.set_password("password")
        self.manager.user.save()
        body = {
            "phone_number": self.manager.user.username[1:],
            "password": "password",
            "device_unique_id": "02515c94de702515c94de7",
            "os": OsTypes.OTHER,
            "os_version": "28",
            "fcm_token": "pM8ChTiUiX6Cr3k-ynmVg3_ZVznyNV5Tty14",
            "last_version": "13",
            "model": "what_model",
            "product": "what_product",
        }
        response = self.client.post(
            reverse("backend:manager_login"),
            body,
            format="json",
        )
        device_data = RegisteredDevice.objects.first()
        self.assertEqual(device_data.user.pk, self.manager.user.pk)
        self.assertEqual(device_data.device_unique_id, body["device_unique_id"])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("municipality_id", response.data)
        self.assertEqual(response.data["municipality_id"], self.manager.municipality.pk)

    @authenticate_manager_test
    def test_manager_permissions(self):
        ManagerHelpers(self.manager, self.municipality).assign_permissions(
            [MunicipalityPermissions.MANAGE_PERMISSIONS]
        )
        data = {
            "phone_number": "22113344",
            "password": "string",
            "name": "string",
            "title": "string",
            "email": "user2@example.com",
            "municipality_id": self.municipality.pk,
            "manage_dossiers": True,
            "manage_procedures": False,
            "manage_complaints": True,
            "manage_reports": False,
            "manage_subject_access_requests": True,
            "manage_committees": False,
            "manage_news": True,
            "manage_events": False,
            "manage_permissions": True,
            "manage_polls": False,
            "manage_forum": True,
            "manage_appointments": False,
            "manage_eticket": True,
        }
        permissions = [
            "MANAGE_COMPLAINTS",
            "MANAGE_DOSSIERS",
            "MANAGE_ETICKET",
            "MANAGE_FORUM",
            "MANAGE_NEWS",
            "MANAGE_PERMISSIONS",
            "MANAGE_SUBJECT_ACCESS_REQUESTS",
        ]
        manager = self.client.post(
            reverse("backend:managers", args=[self.municipality.pk]),
            data,
            format="json",
        )
        self.assertEqual(manager.status_code, 201)

        response = self.client.get(
            reverse("backend:manager", args=[self.municipality.pk, manager.data["id"]])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["permissions"]), 7)
        self.assertEqual(set(response.data["permissions"]), set(permissions))
        data = {
            "municipality_id": 1,
            "name": manager.data["name"],
            "email": manager.data["email"],
            "title": "string",
            "user_id": manager.data["id"],
            "manage_dossiers": False,
            "manage_procedures": False,
            "manage_complaints": False,
            "manage_reports": False,
            "manage_subject_access_requests": False,
            "manage_committees": False,
            "manage_news": False,
            "manage_events": False,
            "manage_permissions": False,
            "manage_appointments": False,
            "manage_polls": False,
            "manage_forum": False,
            "manage_eticket": False,
            "complaint_categories": manager.data["complaint_categories"],
        }
        self.client.put(
            reverse("backend:manager", args=[self.municipality.pk, manager.data["id"]]),
            data,
            format="json",
        )
        response = self.client.get(
            reverse("backend:manager", args=[self.municipality.pk, manager.data["id"]])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["permissions"]), 0)
        self.assertEqual(response.data["permissions"], [])

    def test_complaint_subpermissions_update_self(self):
        category1 = baker.make("backend.complaintcategory", name="the category1")
        category2 = baker.make("backend.complaintcategory", name="2, the category")
        manager = self.make_with_municipality(complaint_categories=[category1])
        self.client.force_authenticate(user=manager.user)  # pylint: disable=no-member
        response = self.client.put(
            self.get_url(manager.user.pk),
            {
                "complaint_categories": [category2.name],
                "manage_complaints": True,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        manager.refresh_from_db()
        self.assertCountEqual(manager.complaint_categories.all(), [category2])

    @authenticate_manager_test
    def test_complaint_subpermissions_update_other_failure(self):
        category1 = baker.make("backend.complaintcategory", name="C1")
        category2 = baker.make("backend.complaintcategory", name="c4")
        manager = self.make_with_municipality(complaint_categories=[category1])

        response = self.client.put(
            self.get_url(manager.user.pk), {"complaint_categories": [category2.name]}
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        manager.refresh_from_db()
        self.assertCountEqual(manager.complaint_categories.all(), [category1])

    @authenticate_manager_test
    def test_complaint_subpermissions_update_other_success(self):
        category1 = baker.make("backend.complaintcategory", name="Trash")
        category2 = baker.make("backend.complaintcategory", name="Tea")
        manager = self.make_with_municipality(complaint_categories=[category1])

        assign_perm(
            MunicipalityPermissions.MANAGE_PERMISSIONS,
            self.manager.user,
            self.municipality,
        )

        response = self.client.put(
            self.get_url(manager.user.pk),
            {
                "complaint_categories": [category2.name],
                "manage_complaints": True,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        manager.refresh_from_db()
        self.assertCountEqual(manager.complaint_categories.all(), [category2])

    def test_send_manager_otp(self):
        """
        assert OTP length >= 4
        """

        self.manager = baker.make(
            "backend.manager",
            user__username=f"M97814709",
            user__first_name=f"rick",
            user__last_name=f"sanchez",
            user__email=f"sanchez@gmail.tn",
            municipality=self.municipality,
        )
        self.manager.user.save()
        phone_number = self.manager.get_phone_number()

        # request send OTP
        response = self.client.post(
            reverse("backend:manager_reset_password"),
            {"phone_number": phone_number, "type": ResetPasswordTypes.SMS},
            format="json",
        )
        OTP = cache.get("{}:{}".format(CachePrefixes.RESET, phone_number))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertGreaterEqual(len(OTP), 4)

    def test_verify_manager_otp(self):
        """
        assert OTP is equal to the value in cache
        assert response contains the manager.user id
        """

        self.manager = baker.make(
            "backend.manager",
            user__username=f"M97814709",
            user__first_name=f"rick",
            user__last_name=f"sanchez",
            user__email=f"sanchez@gmail.tn",
            municipality=self.municipality,
        )
        self.manager.user.save()

        phone_number = self.manager.get_phone_number()
        prepare_reset_password_otp(self.manager.user, phone_number, type="SMS")

        correct_otp = cache.get("{}:{}".format(CachePrefixes.RESET, phone_number))

        # request to verify
        response = self.client.post(
            reverse("backend:manager_reset_password_verify"),
            {"phone_number": phone_number, "otp": correct_otp},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.json()["connected_user_id"], self.manager.user.id)
        self.assertEqual(
            response.json()["municipality_id"], self.manager.municipality.pk
        )

    def test_change_manager_password(self):
        old = "XXXXXXXXXXXX"
        new = "WWWWWWWWWWWW"

        self.manager = baker.make(
            "backend.manager",
            user__username=f"M97814709",
            user__first_name=f"rick",
            user__last_name=f"sanchez",
            user__email=f"sanchez@gmail.tn",
            municipality=self.municipality,
        )
        self.manager.user.set_password(old)
        self.manager.user.save()

        args = [self.municipality.pk, self.manager.user.id]
        self.client.force_authenticate(user=self.manager.user)

        with_old_pass = self.client.post(
            reverse("backend:manager_change_password", args=args),
            {"old_password": old, "new_password": new},
            format="json",
        )
        self.assertEqual(with_old_pass.status_code, status.HTTP_202_ACCEPTED)

        without_old_pass = self.client.post(
            reverse("backend:manager_change_password", args=args),
            {"new_password": new * 2},
            format="json",
        )

        self.assertEqual(without_old_pass.status_code, status.HTTP_202_ACCEPTED)

    @authenticate_manager_test
    @patch("utils.SMSManager.SMSManager.send_sms", return_value=0)
    def test_auto_generate_manager_password(self, mock):
        """
        Assert the creation of two managers without providing a password
        Assert the random password is different for each manager
        """
        assign_perm(
            MunicipalityPermissions.MANAGE_PERMISSIONS,
            self.manager.user,
            self.municipality,
        )
        create_manager = lambda payload: self.client.post(
            reverse("backend:managers", args=[self.municipality.pk]),
            payload,
            format="json",
        )

        manager1 = create_manager(
            {
                "title": "manager",
                "name": "patrick management",
                "phone_number": "55123123",
                "email": "manager1@gmail.tn",
            }
        )
        manager2 = create_manager(
            {
                "title": "also manager",
                "name": "also patrick management",
                "phone_number": "99123123",
                "email": "manager2@gmail.tn",
            }
        )
        self.assertEqual(manager1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(manager2.status_code, status.HTTP_201_CREATED)

        managers = Manager.objects.all()
        self.assertNotEqual(managers[0].user.password, managers[1].user.password)
        self.assertEqual(
            {call.args[0] for call in mock.call_args_list}, {"99123123", "55123123"}
        )
