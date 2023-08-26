from freezegun import freeze_time
from model_bakery import baker
from parameterized import parameterized

from backend.enum import RequestStatus
from backend.models import Municipality
from backend.tests.baker import add_status, bake_updatable
from backend.tests.test_base import TestBase
from backend.tests.test_utils import (
    force_citizen_joined_at,
    force_date_attribute,
    get_random_municipality_id,
    parse_date_aware,
)
from emails.summary import Summary

# The models that are included in the overview (model, related_name)
overview_models = [
    ("complaint", "complaints"),
    ("subjectaccessrequest", "subject_access_requests"),
]


class TestSummary(TestBase):
    def setUp(self):
        self.municipality = Municipality.objects.get(pk=get_random_municipality_id())

    def get_summary(self, date):
        return Summary(parse_date_aware(date), self.municipality.pk).get_full_summary()
        #######################################################################
        #                               Citizens                              #
        #######################################################################

        # Registered###########################################################

    def test_citizens_registered__delta_positive(self):
        self.bake_registered_citizen("2019-02-28")
        self.bake_registered_citizen("2019-03-13")
        ##
        self.bake_registered_citizen("2019-03-30")
        self.bake_registered_citizen("2019-04-02")
        self.bake_registered_citizen("2019-12-30")

        summary = self.get_summary("2019-03-15")
        expected = {"total": 5, "delta": 3}
        self.assertDictEqual(summary["citizens"]["registered"], expected)

    def test_citizens_registered__zero(self):
        self.bake_registered_citizen("2019-07-31")
        self.bake_registered_citizen("2019-08-31")
        self.bake_registered_citizen("2019-11-30")

        summary = self.get_summary("2019-12-31")
        expected = {"total": 3, "delta": 0}
        self.assertDictEqual(summary["citizens"]["registered"], expected)

        # Starred##############################################################

    def test_citizens_starred(self):
        baker.make(
            "backend.citizen", preferred_municipality=self.municipality, _quantity=8
        )
        summary = self.get_summary("2019-03-04")
        self.assertEqual(summary["citizens"]["starred"], 8)

        # Favored##############################################################

    def test_citizens_followed(self):
        citizens = baker.make("backend.citizen", _quantity=9)
        for citizen in citizens:
            citizen.municipalities.add(self.municipality)
        summary = self.get_summary("2019-06-09")
        self.assertEqual(summary["citizens"]["followed"], 9)

        #######################################################################
        #                               Dossiers                              #
        #######################################################################

    def test_dossiers(self):
        self.bake_dossier("2019-02-12")
        self.bake_dossier("2019-01-23")
        self.bake_dossier("2018-04-30")
        self.bake_dossier("2019-04-03")
        self.bake_dossier("2019-05-06")
        self.bake_dossier("2019-08-24")
        summary = self.get_summary("2019-04-14")
        expected = {
            "total": 6,
            "delta": 2,
        }

        self.assertEqual(summary["dossiers"], expected)

        #######################################################################
        #                                 News                                #
        #######################################################################

    def test_news(self):
        self.bake_news("2019-01-21")
        self.bake_news("2019-02-28")
        self.bake_news("2019-11-13")
        self.bake_news("2019-08-25")
        summary = self.get_summary("2019-11-12")
        expected = {
            "total": 4,
            "delta": 1,
        }

        self.assertEqual(summary["news"], expected)

        #######################################################################
        #                                Forum                                #
        #######################################################################

    def test_forum(self):
        post1 = self.bake_post("2019-10-27")
        post2 = self.bake_post("2019-12-13")
        comment1 = self.bake_comment(post1, "2019-10-27")
        self.bake_comment(comment1, "2019-10-29")
        self.bake_comment(comment1, "2019-10-29")
        self.bake_comment(post2, "2019-12-20")

        summary = self.get_summary("2019-10-28")
        expected = {
            "posts": {"total": 2, "delta": 1},
            "comments": {"total": 4, "delta": 3},
        }
        self.assertDictEqual(summary["committees"]["forum"], expected)

        #######################################################################
        #                                Reports                              #
        #######################################################################

    def test_reports__zero(self):
        summary = self.get_summary("2019-10-28")
        expected = {"total": 0, "delta": 0}
        self.assertDictEqual(summary["committees"]["reports"], expected)

    def test_reports__nonzero(self):
        self.bake_report("2019-02-13")
        self.bake_report("2019-01-29")
        self.bake_report("2019-08-30")
        self.bake_report("2019-07-20")

        summary = self.get_summary("2019-06-10")
        expected = {"total": 4, "delta": 2}
        self.assertDictEqual(summary["committees"]["reports"], expected)

        #######################################################################
        #                 Complaints & Subject Access Requests                #
        #######################################################################

    @parameterized.expand(overview_models)
    def test_all(self, model, related_name):
        self.bake_updateable(model, "2019-05-23", RequestStatus.ACCEPTED, "2019-05-30")
        self.bake_updateable(
            model, "2019-02-09", RequestStatus.PROCESSING, "2019-04-23"
        )
        self.bake_updateable(model, "2019-04-07", RequestStatus.REJECTED, "2019-05-01")
        self.bake_updateable(model, "2019-12-01", RequestStatus.ACCEPTED, "2019-12-01")
        self.bake_updateable(model, "2019-12-01", RequestStatus.RECEIVED, "2019-12-01")

        summary = self.get_summary("2019-03-20")
        expected = {"total": 5, "delta": 4}
        self.assertDictEqual(summary[related_name]["all"], expected)

    @parameterized.expand(overview_models)
    def test_status(self, model, related_name):
        self.bake_updateable(
            model, "2019-01-01", RequestStatus.ACCEPTED, "2019-12-31"
        )  # Typical idara
        obj1 = self.bake_updateable(
            model, "2019-11-09", RequestStatus.PROCESSING, "2019-11-10"
        )
        self.add_status(obj1, RequestStatus.REJECTED, "2019-11-30")
        obj2 = self.bake_updateable(
            model, "2019-03-20", RequestStatus.PROCESSING, "2019-05-15"
        )
        self.add_status(obj2, RequestStatus.REJECTED, "2019-05-16")
        self.add_status(obj2, RequestStatus.PROCESSING, "2019-05-18")
        self.add_status(obj2, RequestStatus.ACCEPTED, "2019-05-19")
        self.bake_updateable(model, "2019-04-07", RequestStatus.REJECTED, "2019-05-01")
        self.bake_updateable(model, "2019-12-01", RequestStatus.ACCEPTED, "2019-12-02")
        self.bake_updateable(model, "2019-12-01", RequestStatus.RECEIVED, "2019-12-02")

        summary = self.get_summary("2019-05-18")
        expected = {
            "received": 1,
            "accepted": 3,
            "rejected": 2,
            "processing": 0,
        }
        self.assertDictContainsSubset(expected, summary[related_name])

    @parameterized.expand(overview_models)
    @freeze_time("2019-10-15")
    def test_urgent(self, model, related_name):
        self.bake_updateable(model, "2019-01-01", RequestStatus.ACCEPTED, "2019-10-14")
        obj1 = self.bake_updateable(
            model, "2019-10-10", RequestStatus.RECEIVED, "2019-10-12"
        )
        self.add_status(obj1, RequestStatus.REJECTED, "2019-10-13")
        obj2 = self.bake_updateable(
            model, "2019-03-20", RequestStatus.PROCESSING, "2019-05-15"
        )
        self.add_status(obj2, RequestStatus.ACCEPTED, "2019-05-16")
        self.add_status(obj2, RequestStatus.PROCESSING, "2019-05-18")
        self.add_status(obj2, RequestStatus.REJECTED, "2019-05-19")
        self.bake_updateable(
            model, "2019-09-10", RequestStatus.RECEIVED, "2019-09-11"
        )  #
        obj3 = self.bake_updateable(
            model, "2019-04-10", RequestStatus.RECEIVED, "2019-04-11"
        )
        self.add_status(obj3, RequestStatus.ACCEPTED, "2019-04-20")
        self.add_status(obj3, RequestStatus.PROCESSING, "2019-05-01")  #
        self.bake_updateable(model, "2019-10-15", RequestStatus.RECEIVED, "2019-10-15")
        self.bake_updateable(
            model, "2019-09-29", RequestStatus.PROCESSING, "2019-09-30"
        )

        summary = self.get_summary("2019-09-14")
        self.assertEqual(summary[related_name]["urgent"], 2)

    #######################################################################
    #          Bakery: Don't look here unless you really need to          #
    #######################################################################

    def bake_registered_citizen(self, date):
        return force_citizen_joined_at(
            baker.make("backend.citizen", registration_municipality=self.municipality),
            date,
        )

    def bake_dossier(self, date):
        return force_date_attribute(
            baker.make("backend.dossier", municipality=self.municipality),
            date,
        )

    def bake_post(self, date):
        committee = baker.make("backend.committee", municipality=self.municipality)
        return force_date_attribute(
            baker.make(
                "backend.comment",
                municipality=self.municipality,
                committee=committee,
                parent_comment=None,
            ),
            date,
        )

    def bake_comment(self, parent_comment, date):
        committee = baker.make("backend.committee", municipality=self.municipality)
        return force_date_attribute(
            baker.make(
                "backend.comment",
                parent_comment=parent_comment,
                municipality=self.municipality,
                committee=committee,
            ),
            date,
        )

    def bake_news(self, date):
        return force_date_attribute(
            baker.make("backend.news", municipality=self.municipality),
            date,
            "published_at",
        )

    def bake_report(self, date):
        committee = baker.make("backend.committee", municipality=self.municipality)
        return baker.make(
            "backend.report",
            committee=committee,
            municipality=self.municipality,
            date=parse_date_aware(date),
        )

    def add_status(self, obj, status, status_date):
        return add_status(obj, status, status_date)

    def bake_updateable(self, model: str, date, status, status_date):
        return bake_updatable(
            "backend." + model,
            date,
            status,
            status_date,
            municipality=self.municipality,
        )
