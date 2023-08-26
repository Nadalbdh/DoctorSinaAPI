from django.urls import reverse
from model_bakery import baker

from backend.tests.test_base import authenticate_citizen_test, ElBaladiyaAPITest


class FeedTest(ElBaladiyaAPITest):
    @authenticate_citizen_test
    def test_get_feeds(self):
        baker.make("backend.news", municipality=self.municipality, _quantity=5)
        baker.make("backend.event", municipality=self.municipality, _quantity=15)
        baker.make("backend.report", municipality=self.municipality, _quantity=10)
        response = self.client.get(
            reverse("backend:feeds", args=[self.municipality.id]),
        )
        news = []
        events = []
        reports = []
        for feed in response.json():
            if feed["type"] == "event":
                events.append(feed["object"])
            if feed["type"] == "news_object":
                news.append(feed["object"])
            if feed["type"] == "report":
                reports.append(feed["object"])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(news), 5)
        self.assertEqual(len(reports), 10)
        self.assertEqual(len(events), 15)
        self.assertEqual(len(response.json()), 30)
