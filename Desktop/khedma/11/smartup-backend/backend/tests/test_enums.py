from backend.enum import RequestStatus
from backend.tests.test_base import TestBase


class RequestStatusTest(TestBase):
    def test_get_status_display(self):
        status = [
            "RECEIVED",
            "PROCESSING",
            "ACCEPTED",
            "REJECTED",
            "NOT_CLEAR",
            "INVALID",
        ]
        for idx, s in enumerate(RequestStatus.get_statuses()):
            self.assertEqual(status[idx], s)
