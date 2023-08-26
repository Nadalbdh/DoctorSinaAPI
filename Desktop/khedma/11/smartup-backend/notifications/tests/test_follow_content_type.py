from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from backend.enum import MunicipalityPermissions, RequestStatus
from backend.helpers import ManagerHelpers
from backend.models import OperationUpdate
from backend.tests.test_base import (
    authenticate_citizen_test,
    authenticate_manager_test,
    ElBaladiyaAPITest,
)
from notifications.models import Notification


class NotificationOnFollowAPITest(ElBaladiyaAPITest):
    def test_unauthorized_follow(self):
        urls = [
            "dossiers-follow",
            "complaints-follow",
            "subject-access-requests-follow",
            "comments-follow",
        ]

        for url in urls:
            response = self.client.post(
                reverse(f"notifications:{url}", args=[self.municipality.pk]),
                response_json=False,
            )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_get_followed(self):
        urls = [
            "dossiers-follow",
            "complaints-follow",
            "subject-access-requests-follow",
            "comments-follow",
        ]

        for url in urls:
            response = self.client.get(
                reverse(f"notifications:{url}", args=[self.municipality.pk]),
                response_json=False,
            )
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate_citizen_test
    def test_get_followed_subject(self):
        # make citizen a follower for each contentType
        models = [
            "backend.Dossier",
            "backend.Complaint",
            "backend.SubjectAccessRequest",
            "backend.Comment",
        ]
        instances = [
            baker.make(
                model,
                municipality=self.municipality,
                followers=[self.citizen.user],
            )
            for model in models
        ]
        urls = [
            "dossiers-follow",
            "complaints-follow",
            "subject-access-requests-follow",
            "comments-follow",
        ]

        for url in urls:
            response = self.client.get(
                reverse(f"notifications:{url}", args=[self.municipality.pk]),
                response_json=False,
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data), 1)

    @authenticate_citizen_test
    def test_get_followed_subject_limit(self):
        models = [
            "backend.Dossier",
            "backend.Complaint",
            "backend.SubjectAccessRequest",
            "backend.Comment",
        ]
        [
            baker.make(
                model,
                municipality=self.municipality,
                followers=[self.citizen.user],
                _quantity=11,
            )
            for model in models
        ]
        urls = [
            "dossiers-follow",
            "complaints-follow",
            "subject-access-requests-follow",
            "comments-follow",
        ]

        for url in urls:
            response = self.client.get(
                reverse(f"notifications:{url}", args=[self.municipality.pk]),
                response_json=False,
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data), 10)

    @authenticate_citizen_test
    def test_authorized_follow(self):
        # keep urls and models in the same order
        urls = [
            "complaints-follow",
            "subject-access-requests-follow",
            "comments-follow",
        ]
        models = [
            "backend.Complaint",
            "backend.SubjectAccessRequest",
            "backend.Comment",
        ]
        instances = [
            baker.make(
                model,
                municipality=self.municipality,
            )
            for model in models
        ]

        for idx, url in enumerate(urls):
            response = self.client.post(
                reverse(f"notifications:{url}", args=[self.municipality.pk]),
                {
                    "id": instances[idx].id,
                },
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            self.assertEqual(instances[idx].id, response.data["id"])
            instances[idx].refresh_from_db()
            self.assertEqual(len(instances[idx].followers.all()), 1)
            self.assertEqual(instances[idx].followers.all()[0], self.citizen.user)

    @authenticate_citizen_test
    def test_authorized_follow_dossier(self):
        instance = baker.make(
            "backend.Dossier",
            municipality=self.municipality,
            unique_identifier="999888",
            cin_number="12345678",
        )
        response = self.client.post(
            reverse(f"notifications:dossiers-follow", args=[self.municipality.pk]),
            {
                "unique_identifier": "999888",
                "cin_digits": "678",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(instance.id, response.data["id"])
        instance.refresh_from_db()
        self.assertEqual(len(instance.followers.all()), 1)
        self.assertEqual(instance.followers.all()[0], self.citizen.user)

    @authenticate_citizen_test
    def test_get_is_followed_key_on_each_subject_list(self):
        models = [
            "backend.Complaint",
            "backend.SubjectAccessRequest",
            "backend.Comment",
        ]
        [
            baker.make(
                model,
                id=555,  # used to get single record
                municipality=self.municipality,
                followers=[self.citizen.user],
            )
            for model in models
        ]
        urls = [
            "backend:complaint",
            "backend:subject-access-request",
            "backend:comment",
        ]

        # getting list
        for url in urls:
            response = self.client.get(
                reverse(f"{url}s", args=[self.municipality.pk]),
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data), 1)
            self.assertEqual(len(response.data[0]["followers"]), 1)
            self.assertEqual(response.data[0]["followers"][0], self.citizen.user.id)

        # getting single record
        for url in urls:
            response = self.client.get(
                reverse(url, args=[self.municipality.pk, 555]),
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data["followers"]), 1)
            self.assertEqual(response.data["followers"][0], self.citizen.user.id)

    @authenticate_manager_test
    def test_get_is_followed_key_on_dossier(self):
        ManagerHelpers(self.manager, self.municipality).assign_permissions(
            [MunicipalityPermissions.MANAGE_DOSSIERS]
        )
        dossier = baker.make(
            "backend.Dossier",
            municipality=self.municipality,
            followers=[self.citizen.user],
        )

        # getting Dossier list
        response = self.client.get(
            reverse("backend:dossiers", args=[self.municipality.pk]),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(len(response.data[0]["followers"]), 1)
        self.assertEqual(response.data[0]["followers"][0], self.citizen.user.id)

        # getting Dossier single record
        response = self.client.get(
            reverse("backend:dossier", args=[self.municipality.pk, dossier.id]),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["followers"]), 1)
        self.assertEqual(response.data["followers"][0], self.citizen.user.id)


class OperationUpdateSignalTest(ElBaladiyaAPITest):
    @authenticate_citizen_test
    def test_push_notify_followers_on_dossier_update(self):
        dossier = baker.make(
            "backend.Dossier",
            id=100,
            unique_identifier="123456",
            municipality=self.municipality,
        )
        dossier.followers.add(self.citizen.user)

        OperationUpdate.objects.create(
            operation=dossier,
            status=RequestStatus.ACCEPTED,
            content_type=ContentType.objects.get_for_model(dossier),
        )
        notification = Notification.objects.first()
        self.assertEqual(Notification.objects.count(), 1)

        subject = f"المطلب البلدي الخاص بيك عدد {dossier.unique_identifier}"
        body = f"""تم تحيين وضعية {subject} يمكن تصفح التحديثات عبر حسابك في elBaladiya.tn الرابط: {dossier.citizen_url}"""
        self.assertEqual(
            notification.body,
            body,
        )
