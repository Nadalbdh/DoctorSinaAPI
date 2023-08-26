from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from model_bakery import baker
from rest_framework import status

from backend.tests.test_base import (
    authenticate_citizen_test,
    authenticate_manager_test,
    ElBaladiyaAPITest,
)
from polls.models import ChoiceType

START_DATE = timezone.now() - timedelta(days=1)
END_DATE = timezone.now() + timedelta(days=1)


class PollsTest(ElBaladiyaAPITest):
    def test_polls_votes_count(self):
        baker.make("User", _quantity=2)
        voters_set = baker.make("User", _quantity=2)
        poll = baker.make(
            "polls.Poll",
            text=" Testing polls ? ",
            municipality=self.municipality,
            starts_at=START_DATE,
            ends_at=END_DATE,
        )
        choice = baker.make("polls.Choice", poll=poll, text="yes", voters=voters_set)
        self.assertEqual(choice.votes_count, 2)

    @authenticate_citizen_test
    def test_get_polls(self):
        baker.make(
            "polls.Poll",
            municipality=self.municipality,
            _quantity=8,
            starts_at=START_DATE,
            ends_at=END_DATE,
        )
        response = self.client.get(
            reverse("backend:polls", args=[self.municipality.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 8)

    @authenticate_citizen_test
    def test_create_poll_unauthorized(self):
        data = {
            "text": "hello",
            "starts_at": "2021-11-09T14:06:38.270Z",
            "ends_at": "2021-11-12T14:06:38.270Z",
            "kind": "SINGLE_CHOICE",
        }
        response = self.client.post(
            reverse("backend:polls", args=[self.municipality.id]),
            data=data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate_manager_test
    def test_create_poll(self):
        data = {
            "text": "hello",
            "starts_at": "2021-11-09T14:06:38.270Z",
            "ends_at": "2021-11-12T14:06:38.270Z",
            "kind": "SINGLE_CHOICE",
        }
        response = self.client.post(
            reverse("backend:polls", args=[self.municipality.id]),
            data=data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @authenticate_citizen_test
    def test_single_vote_poll(self):
        poll = baker.make(
            "polls.Poll",
            text="Vote for me?",
            municipality=self.municipality,
            starts_at=START_DATE,
            ends_at=END_DATE,
            kind=ChoiceType.SINGLE_CHOICE.value,
        )
        choice = baker.make("polls.Choice", poll=poll)
        response = self.client.post(
            reverse(
                "backend:choice-vote", args=[self.municipality.id, poll.id, choice.id]
            ),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @authenticate_citizen_test
    def test_multi_vote_poll(self):
        poll = baker.make(
            "polls.Poll",
            text="Vote for me?",
            municipality=self.municipality,
            starts_at=START_DATE,
            ends_at=END_DATE,
        )
        choices = baker.make("polls.Choice", _quantity=2, poll=poll)
        response = self.client.post(
            reverse("backend:poll-vote", args=[self.municipality.id, poll.id])
            + f"?choices={choices[0].pk}&choices={choices[1].pk}",
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @authenticate_citizen_test
    def test_single_vote_poll_out_date(self):
        poll = baker.make(
            "polls.Poll",
            text="Vote for me?",
            municipality=self.municipality,
            starts_at=START_DATE,
            ends_at=START_DATE + timedelta(minutes=5),
            kind=ChoiceType.SINGLE_CHOICE.value,
        )
        choice = baker.make("polls.Choice", poll=poll)
        response = self.client.post(
            reverse(
                "backend:choice-vote", args=[self.municipality.id, poll.id, choice.id]
            ),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @authenticate_manager_test
    def test_create_poll_choice(self):
        poll = baker.make(
            "polls.Poll",
            text="Vote for me?",
            municipality=self.municipality,
            starts_at=START_DATE,
            ends_at=END_DATE,
        )
        data = {
            "text": "hello choice 1",
        }
        response = self.client.post(
            reverse("backend:choices", args=[self.municipality.id, poll.id]),
            data=data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @authenticate_manager_test
    def test_update_poll(self):
        data = {"live_results": True, "kind": "SINGLE_CHOICE"}
        p = baker.make(
            "polls.Poll",
            municipality=self.municipality,
            starts_at=START_DATE,
            ends_at=END_DATE,
        )
        self.assertEqual(p.live_results, False)
        self.assertEqual(p.kind, "MULTI_CHOICE")
        response = self.client.put(
            reverse("backend:poll", args=[self.municipality.id, p.id]),
            data=data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        p.refresh_from_db()
        self.assertEqual(p.live_results, True)
        self.assertEqual(p.kind, "SINGLE_CHOICE")
