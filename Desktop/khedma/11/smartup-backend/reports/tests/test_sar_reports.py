from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from backend.enum import MunicipalityPermissions
from backend.helpers import ManagerHelpers
from backend.models import Municipality
from backend.tests.test_base import ElBaladiyaAPITest
from backend.tests.test_utils import get_random_municipality_id


class TestSarReports(ElBaladiyaAPITest):
    url_name = "reports:sar"
    default_model = "backend.subjectaccessrequest"

    def setUp(self):
        self.manager_data = {
            "email": "admin@gmail.com",
            "password": "test1234",
            "phone_number": "22336644",
        }
        self.municipality = Municipality.objects.get(pk=get_random_municipality_id())
        self.manager = self.__bake_manager(
            [MunicipalityPermissions.MANAGE_SUBJECT_ACCESS_REQUESTS], self.manager_data
        )
        self.make_with_municipality(_quantity=5)

    def test_subject_access_request_report(self):
        bearer = self.get_bearer(self.manager_data)
        response = self.client.get(self.get_query_url(bearer=bearer))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_subject_access_request_report_manager_no_permission(self):
        data = {
            "email": "unauthorized_admin@gmail.com",
            "password": "test1234",
            "phone_number": "22336643",
        }
        self.__bake_manager(
            [MunicipalityPermissions.MANAGE_SUBJECT_ACCESS_REQUESTS], data, False
        )
        bearer = self.get_bearer(data)
        response = self.client.get(self.get_query_url(bearer=bearer))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def user_login(self, data):
        response = self.client.post(
            reverse("backend:manager_login"), data, format="json"
        )
        return response

    def get_bearer(self, data):
        response_login = self.user_login(data)
        self.assertEqual(response_login.status_code, status.HTTP_200_OK)
        return response_login.data["access"]

    def __bake_manager(self, permissions, data, with_permission=True):
        manager = baker.make(
            "backend.manager",
            municipality_id=self.municipality.id,
            user__email=data["email"],
            user__username=self.generateUsernameManager(data["phone_number"]),
            user__is_active=True,
        )
        manager.user.set_password(data["password"])
        manager.user.save()
        if with_permission:
            ManagerHelpers(manager, self.municipality).assign_permissions(permissions)
        return manager

    def get_query_url(self, bearer="", start="", end="", status=""):
        return (
            self.get_url() + f"?status={status}"
            f"&bearer={bearer}&start={start}"
            f"&end={end}"
        )

    def generateUsernameManager(self, username):
        return "M" + username
