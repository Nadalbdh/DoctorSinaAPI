from model_bakery import baker

from backend.models import Event
from backend.tests.test_base import ElBaladiyaAPITest
from notifications.models import Notification


class EventNotificationTest(ElBaladiyaAPITest):
    default_model = "backend.event"

    def test_notification_creation(self):
        baker.make("backend.citizen", _quantity=3, municipalities=[self.municipality])
        baker.make(
            "backend.citizen", _quantity=6, municipalities=[self.other_municipality()]
        )

        self.make_with_municipality()
        notifications = Notification.objects.all()
        self.assertEqual(notifications.count(), 3)
        for notification in notifications:
            self.assertIn("تم إضافة موعد", notification.title)
            self.assertIn("event", str(notification.subject_type))
            self.assertEqual(
                Event.objects.all().first().municipality, notification.municipality
            )
            self.assertEqual(Event.objects.all().first().pk, notification.subject_id)
