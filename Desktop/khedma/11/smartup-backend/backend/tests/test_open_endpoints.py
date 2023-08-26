from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from backend.tests.test_base import ElBaladiyaAPITest
from factories import CitizenFactory


class OpenEndpointsTest(ElBaladiyaAPITest):
    def test_open_endpoint(self):
        url = reverse("backend:municipalities")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_open_endpoint_getter(self):
        url = reverse("backend:procedures", args=[1])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ClosedEndpointsTest(ElBaladiyaAPITest):
    def test_closed_endpoint_unauthorized(self):
        url = reverse("notifications:get_all_notifications")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_closed_endpoint_logged_in(self):
        url = reverse("backend:comments", args=[1])
        user = CitizenFactory().user
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = self.client.post(
            url, data={"title": "a5bar", "body": "barcha a5bar"}
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
