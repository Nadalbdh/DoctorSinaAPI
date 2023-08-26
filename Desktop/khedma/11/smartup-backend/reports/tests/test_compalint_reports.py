from django.urls import reverse
from model_bakery import baker
from rest_framework.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED

from backend.enum import MunicipalityPermissions
from backend.helpers import ManagerHelpers
from backend.models import Municipality
from backend.tests.test_base import ElBaladiyaAPITest
from backend.tests.test_utils import get_random_municipality_id


class TestComplaintReports(ElBaladiyaAPITest):
    url_name = "reports:complaint"
    default_model = "backend.complaint"

    def setUp(self):
        self.manager_data = {
            "email": "admin@gmail.com",
            "password": "test1234",
            "phone_number": "22336644",
        }
        self.municipality = Municipality.objects.get(pk=get_random_municipality_id())
        self.manager = self.__bake_manager(
            [MunicipalityPermissions.MANAGE_COMPLAINTS], self.manager_data
        )
        self.make_with_municipality(_quantity=5)

    def test_complaint_report(self):
        bearer = self.get_bearer(self.manager_data)
        response = self.client.get(self.get_query_url(bearer=bearer))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_complaint_report_with_wrong_params(self):
        bearer = self.get_bearer(self.manager_data)
        response = self.client.get(
            self.get_query_url(
                bearer=bearer, start="soemthingrandom", category="also random"
            )
        )
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_complaint_report_with_category_parameter(self):
        # category is int
        bearer = self.get_bearer(self.manager_data)
        response = self.client.get(self.get_query_url(bearer=bearer, category=1))
        self.assertEqual(response.status_code, HTTP_200_OK)

        # category=none
        bearer = self.get_bearer(self.manager_data)
        response = self.client.get(self.get_query_url(bearer=bearer, category=None))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_complaint_report_manager_no_permission(self):
        data = {
            "email": "unauthorized_admin@gmail.com",
            "password": "test1234",
            "phone_number": "22336643",
        }
        self.__bake_manager([MunicipalityPermissions.MANAGE_COMPLAINTS], data, False)
        bearer = self.get_bearer(data)
        response = self.client.get(self.get_query_url(bearer=bearer))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def user_login(self, data):
        response = self.client.post(
            reverse("backend:manager_login"), data, format="json"
        )
        return response

    def get_bearer(self, data):
        response_login = self.user_login(data)
        self.assertEqual(response_login.status_code, HTTP_200_OK)
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

    def get_query_url(self, bearer="", category="", start="", end="", status=""):
        return (
            self.get_url() + f"?category={category}&status={status}"
            f"&bearer={bearer}&start={start}"
            f"&end={end}"
        )

    def generateUsernameManager(self, username):
        return "M" + username
