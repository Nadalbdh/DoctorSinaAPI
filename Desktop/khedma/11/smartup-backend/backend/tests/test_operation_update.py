from model_bakery import baker

from backend.models import OperationUpdate
from backend.tests.test_base import MunicipalityTestMixin, TestBase


class OperationUpdateTest(MunicipalityTestMixin, TestBase):
    def test_create_operation_update_on_complaint_create(self):
        baker.make("backend.complaint", municipality_id=1)
        self.assertEqual(OperationUpdate.objects.all().count(), 1)

    def test_safe_status_on_none(self):
        comment = self.make_with_municipality("backend.comment")
        comment.operation_updates.all().delete()
        self.assertIsNone(comment.last_operation_update)
        self.assertIsNone(comment.status)
