from model_bakery import baker

from backend.models import Committee

from .test_base import TestBase
from .test_utils import get_random_municipality_id


class CommitteeTest(TestBase):
    def test_committees_order(self):
        municipality_id = get_random_municipality_id()
        town_council = baker.make(
            "backend.Committee", title="المجلس البلدي", municipality_id=municipality_id
        )
        baker.make("backend.committee", _quantity=10, municipality_id=municipality_id)
        returned_committees = Committee.objects.all()
        self.assertEqual(returned_committees[0].pk, town_council.pk)
