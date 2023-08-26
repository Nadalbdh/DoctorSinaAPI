from model_bakery import baker

from backend.models import Municipality
from backend.tests.test_base import TestBase
from backend.tests.test_utils import get_random_municipality_id


class MunicipalityTest(TestBase):
    def setUp(self):
        self.municipality = Municipality.objects.get(pk=get_random_municipality_id())

    def test_emails_list(self):
        emails = baker.make("emails.Email", municipality=self.municipality, _quantity=8)
        emails_list = [email.email for email in emails]
        self.assertCountEqual(emails_list, self.municipality.summary_email_list())


class ComplaintTest(TestBase):
    def setUp(self):
        self.municipality = Municipality.objects.get(pk=get_random_municipality_id())

    def test_sub_comments(self):
        parent = baker.make("backend.Comment", municipality=self.municipality)
        baker.make(
            "backend.Comment",
            parent_comment=parent,
            municipality=self.municipality,
            _quantity=4,
        )
        self.assertEqual(4, parent.sub_comments.count())
