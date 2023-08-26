from model_bakery import baker

from backend.models import Municipality
from backend.tests.test_base import TestBase
from backend.tests.test_utils import get_random_municipality_id
from emails.helpers.mailing_list import update_mailing_list


class TestSummary(TestBase):
    def setUp(self):
        self.municipality = Municipality.objects.get(pk=get_random_municipality_id())

    def test_empty(self):
        baker.make(
            "emails.Email",
            municipality=self.municipality,
            email=self.fake.email,
            _quantity=13,
        )
        self.assertEqual(self.municipality.emails.count(), 13)
        update_mailing_list(self.municipality, [])
        self.assertEqual(self.municipality.emails.count(), 0)

    def test_no_intersection(self):
        self.municipality.emails.create(email="georgescott@frank-hawkins.biz")
        self.municipality.emails.create(email="daniellawson@yahoo.com")
        self.municipality.emails.create(email="wcampbell@hotmail.com")
        new_list = [
            "woodrebecca@powers.net",
            "krausekathleen@thomas.net",
            "egomez@fletcher-schroeder.info",
            "tammie72@hotmail.com",
            "dustinbrown@martinez.com",
        ]
        update_mailing_list(self.municipality, new_list)
        self.assertCountEqual(self.municipality.summary_email_list(), new_list)

    def test_intersection(self):
        self.municipality.emails.create(email="wcastillo@powell-bernard.net")
        self.municipality.emails.create(email="pacosta@yahoo.com")
        self.municipality.emails.create(email="brittanyhenderson@yahoo.com")
        self.municipality.emails.create(email="adaniels@wright.com")
        new_list = [
            "brittanyhenderson@yahoo.com",
            "adaniels@wright.com",
            "luis36@hotmail.com",
            "cameronvelasquez@jones-lara.com",
        ]

        update_mailing_list(self.municipality, new_list)
        self.assertCountEqual(self.municipality.summary_email_list(), new_list)
