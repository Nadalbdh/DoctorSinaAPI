from model_bakery import baker

from api_logger.models import APILog
from backend.tests.test_base import ElBaladiyaAPITest


class APILogTest(ElBaladiyaAPITest):
    def setUp(self):
        super().setUp()

    def test_logs_persistence_after_user_deletion(self):
        baker.make("api_logger.apilog", _quantity=10, user=self.citizen.user)
        self.assertEqual(APILog.objects.all().count(), 10)
        self.assertEqual(APILog.objects.first().user, self.citizen.user)
        self.citizen.user.delete()
        self.assertEqual(APILog.objects.all().count(), 10)
        self.assertEqual(APILog.objects.first().user, None)
