from backend.tests.test_base import authenticate_citizen_test, ElBaladiyaAPITest


class EventTest(ElBaladiyaAPITest):
    default_model = "backend.event"
    url_name = "backend:event"

    @authenticate_citizen_test
    def test_add_interested(self):
        event = self.make_with_municipality(
            title="conference",
            description="launching conference for ElBaladiya.tn",
            starting_date="2021-10-19",
        )
        data = {"interest": "True"}
        self.client.post("%s/interest" % self.get_url(event.pk), data, format="json")
        event.refresh_from_db()
        self.assertCountEqual(event.interested_citizen.all(), [self.citizen])

    @authenticate_citizen_test
    def test_remove_interested(self):
        event = self.make_with_municipality(
            title="conference",
            description="launching conference for ElBaladiya.tn",
            starting_date="2021-10-19",
        )
        event.interested_citizen.add(self.citizen)
        data = {"interest": "False"}
        self.client.post("%s/interest" % self.get_url(event.pk), data, format="json")

        event.refresh_from_db()
        self.assertCountEqual(event.interested_citizen.all(), [])

    @authenticate_citizen_test
    def test_participate(self):
        event = self.make_with_municipality(
            title="conference",
            description="launching conference for ElBaladiya.tn",
            starting_date="2021-10-19",
        )
        data = {"participate": "True"}
        self.client.post("%s/participate" % self.get_url(event.pk), data, format="json")
        event.refresh_from_db()
        self.assertCountEqual(event.participants.all(), [self.citizen])

    @authenticate_citizen_test
    def test_remove_participant(self):
        event = self.make_with_municipality(
            title="conference",
            description="launching conference for ElBaladiya.tn",
            starting_date="2021-10-19",
        )
        event.participants.add(self.citizen)
        data = {"participate": "False"}
        self.client.post("%s/participate" % self.get_url(event.pk), data, format="json")

        event.refresh_from_db()
        self.assertCountEqual(event.participants.all(), [])

    @authenticate_citizen_test
    def test_deprecated_unparticipate(self):
        event = self.make_with_municipality(
            title="conference",
            description="launching conference for ElBaladiya.tn",
            starting_date="2021-10-19",
        )
        event.participants.add(self.citizen)

        self.client.post(
            "%s/unparticipate" % self.get_url(event.pk),
        )

        event.refresh_from_db()
        self.assertCountEqual(event.participants.all(), [])

    @authenticate_citizen_test
    def test_deprecated_participate(self):
        event = self.make_with_municipality(
            title="conference",
            description="launching conference for ElBaladiya.tn",
            starting_date="2021-10-19",
        )
        self.client.post(
            "%s/participate" % self.get_url(event.pk),
        )

        event.refresh_from_db()
        self.assertCountEqual(event.participants.all(), [self.citizen])

    @authenticate_citizen_test
    def test_deprecated_disinterest(self):
        event = self.make_with_municipality(
            title="conference",
            description="launching conference for ElBaladiya.tn",
            starting_date="2021-10-19",
        )
        event.interested_citizen.add(self.citizen)

        self.client.post(
            "%s/disinterest" % self.get_url(event.pk),
        )

        event.refresh_from_db()
        self.assertCountEqual(event.interested_citizen.all(), [])

    @authenticate_citizen_test
    def test_deprecated_interest(self):
        event = self.make_with_municipality(
            title="conference",
            description="launching conference for ElBaladiya.tn",
            starting_date="2021-10-19",
        )
        self.client.post(
            "%s/interest" % self.get_url(event.pk),
        )
        event.refresh_from_db()
        self.assertCountEqual(event.interested_citizen.all(), [self.citizen])
