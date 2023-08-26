from unittest.mock import patch

from django.urls import reverse
from guardian.shortcuts import assign_perm
from model_bakery import baker
from rest_framework import status

from backend.enum import MunicipalityPermissions
from backend.tests.test_base import (
    authenticate_citizen_test,
    authenticate_manager_test,
    ElBaladiyaAPITest,
)
from notifications.models import Notification


class NotificationAPITestForCitizen(ElBaladiyaAPITest):
    @authenticate_citizen_test
    def test_mark_as_read(self):
        user = self.citizen.user
        baker.make("notifications.notification", user=user, is_read=True, _quantity=4)
        baker.make("notifications.notification", user=user, is_read=False, _quantity=5)
        response = self.client.post(
            reverse("notifications:mark_notifications_as_read"), response_json=False
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        notifications = user.notifications.all()
        self.assertEqual(9, len(notifications))
        for notification in notifications:
            self.assertTrue(notification.is_read)

    @authenticate_citizen_test
    def test_mark_single_notification_as_read(self):
        user = self.citizen.user
        notif = baker.make("notifications.notification", user=user, is_read=False)

        self.assertFalse(notif.is_read)
        response = self.client.post(
            reverse("notifications:mark_single_notification_as_read", args=[notif.pk]),
            response_json=False,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        notification = user.notifications.filter(id=notif.pk).first()
        self.assertTrue(notification.is_read)

    @authenticate_citizen_test
    def test_get_notification_by_id(self):
        user = self.citizen.user
        notif = baker.make("notifications.notification", user=user, is_read=False)
        response = self.client.get(
            reverse("notifications:get_notification", args=[notif.pk])
        )
        fields = {
            "id",
            "title",
            "body",
            "is_read",
            "created_at",
            "subject_id",
            "action_param",
            "action_type",
            "user",
            "subject_type",
            "municipality",
            "is_sent",
            "model",
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.keys(), fields)

    @authenticate_citizen_test
    def test_get_all_notifications(self):
        user = self.citizen.user
        baker.make("notifications.notification", user=user, is_read=True, _quantity=4)
        baker.make("notifications.notification", user=user, is_read=False, _quantity=5)

        response = self.client.get(
            reverse("notifications:get_all_notifications"),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data["notifications"]), 9)


class NotificationAPITestForManager(ElBaladiyaAPITest):
    @authenticate_manager_test
    def test_mark_as_read(self):
        user = self.manager.user
        baker.make("notifications.notification", user=user, is_read=True, _quantity=4)
        baker.make("notifications.notification", user=user, is_read=False, _quantity=5)
        response = self.client.post(
            reverse("notifications:mark_notifications_as_read"), response_json=False
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        notifications = user.notifications.all()
        self.assertEqual(9, len(notifications))
        for notification in notifications:
            self.assertTrue(notification.is_read)

    @authenticate_manager_test
    def test_mark_single_notification_as_read(self):
        user = self.manager.user
        notif = baker.make("notifications.notification", user=user, is_read=False)

        self.assertFalse(notif.is_read)
        response = self.client.post(
            reverse("notifications:mark_single_notification_as_read", args=[notif.pk]),
            response_json=False,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        notification = user.notifications.filter(id=notif.pk).first()
        self.assertTrue(notification.is_read)

    @authenticate_manager_test
    def test_get_notification_by_id(self):
        user = self.manager.user
        notif = baker.make("notifications.notification", user=user, is_read=False)
        response = self.client.get(
            reverse("notifications:get_notification", args=[notif.pk])
        )
        fields = {
            "id",
            "title",
            "body",
            "is_read",
            "created_at",
            "subject_id",
            "action_param",
            "action_type",
            "user",
            "subject_type",
            "municipality",
            "is_sent",
            "model",
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.keys(), fields)

    @authenticate_manager_test
    def test_get_all_notifications(self):
        user = self.manager.user
        baker.make("notifications.notification", user=user, is_read=True, _quantity=4)
        baker.make("notifications.notification", user=user, is_read=False, _quantity=5)

        response = self.client.get(
            reverse("notifications:get_all_notifications"),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data["notifications"]), 9)

    def test_get_all_notifications_not_authenticated_user(self):
        user = self.manager.user
        baker.make("notifications.notification", user=user, is_read=True, _quantity=4)
        baker.make("notifications.notification", user=user, is_read=False, _quantity=5)

        response = self.client.get(
            reverse("notifications:get_all_notifications"),
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_notification_by_id_not_authenticated_user(self):
        user = self.manager.user
        notif = baker.make("notifications.notification", user=user, is_read=False)
        response = self.client.get(
            reverse("notifications:get_notification", args=[notif.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class NotificationSignalTest(ElBaladiyaAPITest):
    def test_notify_manager_signal_triggered(self):
        """
        assert notification.user is a manager with proper < permission >
        assert notification objects are being saved with each < notifiable_model > instance created
        """
        notifiables = [
            [MunicipalityPermissions.MANAGE_DOSSIERS, "backend.Dossier"],
            [
                MunicipalityPermissions.MANAGE_SUBJECT_ACCESS_REQUESTS,
                "backend.SubjectAccessRequest",
            ],
            [MunicipalityPermissions.MANAGE_FORUM, "backend.Comment"],
            [MunicipalityPermissions.MANAGE_COMPLAINTS, "backend.Complaint"],
        ]

        for notifiable in notifiables:
            permission, notifiable_model = notifiable
            assign_perm(permission, self.manager.user, self.municipality)
            baker.make(
                notifiable_model,
                municipality=self.municipality,
            )
            self.assertEqual(Notification.objects.last().user, self.manager.user)
            self.assertEqual(
                Notification.objects.last().municipality.id, self.municipality.id
            )

        self.assertEqual(
            Notification.objects.filter(user=self.manager.user).count(),
            len(notifiables),
        )
