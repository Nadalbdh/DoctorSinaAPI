from rest_framework import status

from backend import models
from backend.enum import TopicStates
from backend.serializers import serializers
from backend.tests.test_base import (
    authenticate_citizen_test,
    authenticate_manager_test,
    ElBaladiyaAPITest,
)
from backend.tests.test_utils import get_random_municipality_id


class TopicTest(ElBaladiyaAPITest):
    url_name = "backend:topic"
    default_model = "backend.topic"

    def test_get_topics(self):
        self.make_with_municipality(_quantity=5)
        response = self.client.get(self.get_url(), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

    def test_get_topic(self):
        topic = self.make_with_municipality(
            label="9hawi", state=TopicStates.ACTIVATED, description="Chbihom l 9hawi?"
        )

        response = self.client.get(self.get_url(topic.pk), format="json")

        expected = {
            "label": "9hawi",
            "description": "Chbihom l 9hawi?",
            "municipality": self.municipality.pk,
        }

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictContainsSubset(expected, response.data)

    @authenticate_manager_test
    def test_create_topic(self):
        data = {
            "label": "label topic",
            "description": "hello",
            "state": TopicStates.ARCHIVED,
        }

        response = self.client.post(self.get_url(), data, format="json")
        # Status
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Correct topic returned
        data["municipality"] = self.municipality.pk
        self.assertDictContainsSubset(data, response.data)

        # Topic actually created
        topic = models.Topic.objects.last()
        self.assertEqual(serializers.TopicSerializer(topic).data, response.data)

    @authenticate_manager_test
    def test_update_topic(self):
        topic = self.make_with_municipality(
            description="Broke", state=TopicStates.HIDDEN, label="Financial Status"
        )

        data = {"description": "Woke", "state": TopicStates.ACTIVATED}
        response = self.client.put(self.get_url(topic.pk), data, format="json")

        expected = {
            "description": "Woke",
            "state": TopicStates.ACTIVATED,
            "label": "Financial Status",
            "id": topic.pk,
            "municipality": self.municipality.pk,
        }

        # Correct data is returned
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictContainsSubset(expected, response.data)

        topic.refresh_from_db()
        self.assertEqual(serializers.TopicSerializer(topic).data, response.data)

    @authenticate_manager_test
    def test_delete_topic(self):
        topic = self.make_with_municipality()
        method = self.client.delete
        response = method(self.get_url(topic.pk), response_json=False, format="json")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(models.Topic.objects.filter(pk=topic.pk).exists())

    def test_not_found(self):
        response = self.client.get(self.get_url(420), format="json")
        self.assertNotFoundResponse(response)

    @authenticate_citizen_test
    def test_create_topic_citizen(self):
        data = {
            "label": "label topic",
            "description": "",
            "state": TopicStates.ARCHIVED,
        }
        response = self.client.post(self.get_url(), data, format="json")

        self.assertForbiddenResponse(response)
        self.assertFalse(models.Topic.objects.filter(label="label topic").exists())

    @authenticate_citizen_test
    def test_update_topic_citizen(self):
        topic = self.make_with_municipality(state=TopicStates.HIDDEN)

        data = {
            "state": TopicStates.ACTIVATED,
        }

        response = self.client.put(self.get_url(topic.pk), data, format="json")
        # Status
        self.assertForbiddenResponse(response)

        topic.refresh_from_db()
        self.assertEqual(topic.state, TopicStates.HIDDEN)

    @authenticate_citizen_test
    def test_delete_topic_citizen(self):
        topic = self.make_with_municipality()

        response = self.client.delete(
            self.get_url(topic.pk), response_json=False, format="json"
        )

        # Status
        self.assertForbiddenResponse(response)
        topic.refresh_from_db()

    @authenticate_manager_test
    def test_create_topic_in_another_municipality(self):
        # Change the municipality
        other_id = get_random_municipality_id()
        while other_id == self.municipality.pk:
            other_id = get_random_municipality_id()
        self.municipality = models.Municipality.objects.get(pk=other_id)

        data = {
            "label": "glace",
            "description": "l glace.",
            "state": TopicStates.ARCHIVED,
        }

        response = self.client.post(self.get_url(), data, format="json")

        self.assertForbiddenResponse(response)
        self.assertFalse(models.Topic.objects.filter(label="glace").exists())
