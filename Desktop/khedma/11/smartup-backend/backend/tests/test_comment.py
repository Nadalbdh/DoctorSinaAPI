import json
from unittest.mock import patch

from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from backend.enum import ForumTypes, RequestStatus
from backend.models import Comment, Municipality
from backend.tests.test_base import ElBaladiyaAPITest
from backend.tests.test_utils import check_equal_attributes


# FIXME Refactor
class CommentTest(ElBaladiyaAPITest):
    def setUp(self):
        self.municipality_id = 1
        self.municipality = Municipality.objects.get(pk=self.municipality_id)
        self.manager = self.make_manager()

    def test_get_comments(self):
        self.bake_comment(self.manager.user)
        self.bake_comment(self.manager.user, topic_label="random topic 1")
        self.bake_comment(self.manager.user, topic_label="random topic 12")
        self.client.force_authenticate(user=self.manager.user)
        comments = self.municipality.all_comments.all()
        response = self.client.get(
            reverse("backend:comments", args=[self.municipality_id])
        )
        response_obj = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_obj), len(comments))

    def test_get_comment(self):
        comment = self.bake_comment(self.manager.user)
        self.client.force_authenticate(user=self.manager.user)
        url = reverse("backend:comment", args=[self.municipality_id, comment.pk])
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            check_equal_attributes(
                comment, response.data, ["body", "title", "municipality_id"]
            )
        )

    def test_create_comment(self):
        self.client.force_authenticate(user=self.manager.user)
        topic_id = self.bake_topic().pk

        data = {
            "municipality_id": self.municipality_id,
            "topic": topic_id,
            "title": "POST_CORRECT",
            "body": "POST_CORRECT_BODY",
            "type": ForumTypes.SUGGESTION,
        }
        url = reverse("backend:comments", args=[self.municipality_id])
        response = self.client.post(url, data, format="json")
        comment = Comment.objects.last()
        # Status
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # check returned object against db object
        self.assertTrue(
            check_equal_attributes(
                comment, response.data, ["body", "title", "municipality_id", "type"]
            )
        )

        # check db object against initial object
        self.assertTrue(
            check_equal_attributes(
                comment,
                data,
                ["body", "title", "municipality_id", "type"],
            )
        )

    def test_update_comment(self):
        self.client.force_authenticate(user=self.manager.user)
        comment = self.bake_comment(self.manager.user)
        topic_id = self.bake_topic(label="Another topic").pk
        old_object = comment.to_dict()
        data = {"body": "CHANGED", "type": ForumTypes.QUESTION, "topic": topic_id}
        url = reverse("backend:comment", args=[self.municipality_id, comment.pk])
        response = self.client.put(url, data)
        comment.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # only specified attributes changed
        self.assertTrue(
            check_equal_attributes(comment, old_object, ["title", "municipality_id"])
        )
        # check if the returned object matches the db object
        self.assertTrue(
            check_equal_attributes(
                comment, response.data, ["body", "type", "municipality_id"]
            )
        )
        # check that the new value is inserted
        self.assertEqual("CHANGED", response.data["body"])
        self.assertEqual(ForumTypes.QUESTION, response.data["type"])

    def test_update_comment_status(self):
        self.client.force_authenticate(user=self.manager.user)
        comment = self.bake_comment(self.manager.user)
        data = {
            "id": comment.pk,
            "image": "data:image/png;base64,R0lGODlhAQABAAAAACw=",
            "status": RequestStatus.PROCESSING,
            "note": "test note",
        }
        url = reverse("backend:comment-status", args=[self.municipality_id, comment.pk])
        response = self.client.post(url, data)
        comment.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # only specified attributes changed
        self.assertEqual(comment.status, RequestStatus.PROCESSING)

    def test_delete_comment(self):
        self.client.force_authenticate(user=self.manager.user)
        comment = Comment.objects.create(
            created_by=self.manager.user,
            municipality_id=self.municipality_id,
            title="TEST_Create",
            body="THIS IS A Create TEST",
            type=ForumTypes.SUGGESTION,
        )
        comment.save()

        url = reverse("backend:comment", args=[self.municipality_id, comment.pk])
        response = self.client.delete(url, response_json=False)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())

    def test_not_found(self):
        url = reverse("backend:comment", args=[self.municipality.id, 420])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # any user has the right to delete comments of others? euhhh
    def test_update_delete_comment_of_others(self):
        pass
        # self.client.force_authenticate(user=self.manager.user)
        # # Comment created by another user
        # another_manager = self.make_manager()
        # self.bake_comment(another_manager.user)
        # comment = Comment.objects.last()
        # old_object = comment.to_dict()
        # data = {"body": "CHANGED", "type": ForumTypes.QUESTION}
        # method = self.client.put
        # url = reverse("backend:comment", args=[self.municipality_id, comment.pk])
        # response = TestRequest(method, url, data).perform()
        # # Status
        # self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        #
        # method = self.client.delete
        # url = reverse("backend:comment", args=[self.municipality_id, comment.pk])
        # response = TestRequest(method, url, response_json=False).perform()
        # # Status
        # self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def make_manager(self):
        # set up manager rights
        manager = baker.make("backend.manager", municipality=self.municipality)
        return manager

    def bake_comment(self, user, topic_label="Title"):
        return baker.make(
            "backend.comment",
            topic=self.bake_topic(label=topic_label),
            municipality=self.municipality,
            body="not empty",
            created_by=user,
        )

    def bake_topic(self, label="Title"):
        return baker.make("backend.topic", label=label, municipality=self.municipality)
