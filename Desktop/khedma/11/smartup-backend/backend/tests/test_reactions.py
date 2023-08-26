from django.urls import reverse
from model_bakery import baker

from backend.enum import NewsCategory
from backend.models import Reaction
from backend.tests.test_base import authenticate_citizen_test, ElBaladiyaAPITest


class ReactionTest(ElBaladiyaAPITest):
    @authenticate_citizen_test
    def test_add_reaction_news(self):
        new = baker.make(
            "backend.news",
            municipality=self.municipality,
            category=NewsCategory.ANNOUNCEMENT,
        )
        response = self.client.post(
            reverse("backend:reactions"),
            {"type": "L", "value": 0, "post_type": "NEWS", "post_id": new.pk},
            format="json",
        )
        reaction = Reaction.objects.filter(type="L", value=0, object_id=new.pk)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(reaction.exists())

    @authenticate_citizen_test
    def test_add_reaction_comments(self):
        comment = baker.make("backend.comment", municipality=self.municipality)
        response = self.client.post(
            reverse("backend:reactions"),
            {"type": "L", "value": 0, "post_type": "COMMENT", "post_id": comment.pk},
            format="json",
        )
        reaction = Reaction.objects.filter(type="L", value=0, object_id=comment.pk)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(reaction.exists())

    @authenticate_citizen_test
    def test_add_reaction_complaints(self):
        complaint = baker.make("backend.complaint", municipality=self.municipality)
        response = self.client.post(
            reverse("backend:reactions"),
            {
                "type": "L",
                "value": 0,
                "post_type": "COMPLAINT",
                "post_id": complaint.pk,
            },
            format="json",
        )
        reaction = Reaction.objects.filter(type="L", value=0, object_id=complaint.pk)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(reaction.exists())
