from django.urls import reverse
from model_bakery import baker
from rest_framework import status
from rest_framework_api_key.models import APIKey

from backend.enum import MunicipalityPermissions
from backend.helpers import ManagerHelpers
from backend.tests.test_base import ElBaladiyaAPITest


class ServicesTest(ElBaladiyaAPITest):
    def setUp(self):
        super().setUp()
        self.api_key, self.key = APIKey.objects.create_key(name="remote-service")
        self.__bake_manager(
            [MunicipalityPermissions.MANAGE_ETICKET],
            {
                "email": "admin@gmail.com",
                "password": "test1234",
                "phone_number": "22336644",
            },
        )
        self.agency = baker.make(
            "etickets_v2.Agency",
            municipality=self.municipality,
        )

    def test_local_server_get_manager_auth_with_token(self):
        response = self.client.get(
            reverse("backend:managers", args=[self.municipality.pk]),
            HTTP_AUTHORIZATION=f"Api-Key {self.key}",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # only asserting on the managers created in setUp
        # since he has proper permission on the municipality object
        self.assertEqual(len(response.data), 1)

    def __bake_manager(self, permissions, data, with_permission=True):
        manager = baker.make(
            "backend.manager",
            municipality_id=self.municipality.id,
            user__email=data["email"],
            user__username="M97814709",
            user__is_active=True,
        )
        manager.user.set_password(data["password"])
        manager.user.save()
        if with_permission:
            ManagerHelpers(manager, self.municipality).assign_permissions(permissions)
        return manager
