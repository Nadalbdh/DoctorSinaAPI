from django.urls import reverse
from model_bakery import baker

from backend.tests.test_base import authenticate_citizen_test, ElBaladiyaAPITest


class StaticTextTest(ElBaladiyaAPITest):
    @authenticate_citizen_test
    def test_get_all_static_texts(self):
        baker.make("backend.statictext", _quantity=8)
        response = self.client.get(
            reverse("backend:static-texts"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 8)

    @authenticate_citizen_test
    def test_get_static_text_by_topic(self):
        static_text = baker.make(
            "backend.statictext",
            topic="electricity prblm",
            title="elec",
            body="Hello there!",
        )
        response = self.client.get(
            reverse("backend:static-text", args=[static_text.topic])
        )
        data = {"topic": "electricity prblm", "title": "elec", "body": "Hello there!"}
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, data)
