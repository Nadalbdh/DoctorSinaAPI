from django.urls import reverse
from model_bakery import baker

from backend.tests.test_base import authenticate_citizen_test, ElBaladiyaAPITest


class NewsTagsTest(ElBaladiyaAPITest):
    @authenticate_citizen_test
    def test_get_all_news_tags(self):
        baker.make("backend.newstag", _quantity=8)
        response = self.client.get(
            reverse("backend:news-tags"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 8)

    @authenticate_citizen_test
    def test_get_news_tag_by_name(self):
        news_tag = baker.make("backend.newstag", name="IamNewsTag")
        response = self.client.get(reverse("backend:news-tag", args=[news_tag.name]))
        data = {"id": news_tag.id, "name": "IamNewsTag"}
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, data)
