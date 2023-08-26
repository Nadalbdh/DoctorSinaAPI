from datetime import datetime

from django.contrib.auth.models import User
from django.urls import reverse
from freezegun import freeze_time
from guardian.shortcuts import assign_perm
from model_bakery import baker
from rest_framework import status

from backend.tests.test_base import (
    authenticate_citizen_test,
    authenticate_manager_test,
    ElBaladiyaAPITest,
)


class DeleteAccountTest(ElBaladiyaAPITest):
    @freeze_time("2021-01-12")
    @authenticate_citizen_test
    def test_delete_account_citizen(self):
        self.assertFalse(self.citizen.is_deleted)
        self.assertTrue(self.citizen.user.is_active)
        current_timestamp = datetime.timestamp(datetime.now())
        newname = self.citizen.user.username + ";deleted;" + str(current_timestamp)
        response = self.client.delete(reverse("backend:delete-account"))
        self.assertEqual(response.status_code, 204)
        user = User.objects.get(id=self.citizen.user.pk)
        self.assertFalse(user.is_active)
        self.assertTrue(user.citizen.is_deleted)
        self.assertEqual(user.username, newname)

    @freeze_time("2021-01-12")
    @authenticate_manager_test
    def test_delete_account_manager(self):
        self.assertFalse(self.manager.is_deleted)
        self.assertTrue(self.manager.user.is_active)
        current_timestamp = datetime.timestamp(datetime.now())
        newname = self.manager.user.username + ";deleted;" + str(current_timestamp)
        response = self.client.delete(reverse("backend:delete-account"))
        self.assertEqual(response.status_code, 204)
        user = User.objects.get(id=self.manager.user.pk)
        self.assertFalse(user.is_active)
        self.assertTrue(user.manager.is_deleted)
        self.assertEqual(user.username, newname)

    @freeze_time("2021-01-12")
    def test_delete_account_other_managers(self):
        manager = baker.make(
            "backend.manager",
            user__username="M0000000",
            user__is_active=True,
            municipality=self.municipality,
        )
        manager1 = baker.make(
            "backend.manager",
            user__username="M111111111",
            user__is_active=True,
            municipality=self.municipality,
        )
        self.client.force_login(user=manager.user)
        response = self.client.delete(
            reverse(
                "backend:delete-manager-account",
                args=[self.municipality.id, manager1.id],
            )
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        assign_perm("MANAGE_PERMISSIONS", manager.user, self.municipality)

        response = self.client.delete(
            reverse(
                "backend:delete-manager-account",
                args=[self.municipality.id, manager1.id],
            )
        )
        self.assertTrue(manager.user.has_perm("MANAGE_PERMISSIONS", self.municipality))
        self.assertEqual(response.status_code, 204)
        user = User.objects.get(id=manager1.user.pk)
        self.assertFalse(user.is_active)
        self.assertTrue(user.manager.is_deleted)
