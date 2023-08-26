from model_bakery import baker
from rest_framework import status

from backend.enum import NewsCategory
from backend.tests.test_base import (
    authenticate_citizen_test,
    authenticate_manager_test,
    ElBaladiyaAPITest,
    TestBase,
)
from notifications.models import Notification


class NewsTest(TestBase):
    """
    Scenario:
        1) Create a municipality
        2) Create a citizen, and follow the created municipality
        3) Create a News to broadcast, make sure the citizen received the notification
    """

    def test_notifications_sent_on_broadcast_news(self):
        municipality = baker.make("backend.municipality")
        citizen = baker.make("backend.citizen")
        citizen.municipalities.add(municipality)
        citizen.save()
        baker.make("backend.news", municipality=municipality, to_broadcast=True)
        self.assertEqual(Notification.objects.all().count(), 1)
        self.assertEqual(
            Notification.objects.all().first().municipality.id, municipality.id
        )


class NewsViewTest(ElBaladiyaAPITest):
    url_name = "backend:news"

    @authenticate_manager_test
    def test_edit_category(self):
        news = baker.make(
            "backend.news",
            municipality=self.municipality,
            category=NewsCategory.ANNOUNCEMENT,
        )

        new_category = NewsCategory.ACTIVITIES_AND_EVENTS

        response = self.client.put(self.get_url(news.pk), {"category": new_category})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        news.refresh_from_db()
        self.assertEqual(news.category, new_category)

    @authenticate_manager_test
    def test_edit_no_category(self):
        news = baker.make(
            "backend.news",
            municipality=self.municipality,
            category=NewsCategory.CALL_FOR_TENDER,
        )

        new_body = "hehe"

        response = self.client.put(self.get_url(news.pk), {"body": new_body})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        news.refresh_from_db()
        self.assertEqual(news.body, new_body)
        self.assertEqual(news.category, NewsCategory.CALL_FOR_TENDER)

    @authenticate_citizen_test
    def test_edit_category_citizen(self):
        news = baker.make(
            "backend.news",
            municipality=self.municipality,
            category=NewsCategory.ANNOUNCEMENT,
        )

        new_category = NewsCategory.ACTIVITIES_AND_EVENTS

        response = self.client.put(self.get_url(news.pk), {"category": new_category})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        news.refresh_from_db()
        self.assertEqual(news.category, NewsCategory.ANNOUNCEMENT)
