from django.db import IntegrityError
from model_bakery import baker

from backend.models import Municipality
from backend.tests.test_base import TestBase
from backend.tests.test_utils import get_random_municipality_id
from sms.enum import SMSQueueStatus
from sms.models import SMSQueueElement
from sms.sms_manager import SMSManager


class SMSQueueModelTest(TestBase):
    def setUp(self):
        self.municipality = Municipality.objects.get(pk=get_random_municipality_id())

    def test_create_constraint(self):
        try:
            baker.make_recipe("sms.pending_sms", municipality=None)
            self.fail("No exception raised. Expected Integrity Error")
        except IntegrityError:
            pass

    def test_update_constraint(self):
        sms_obj = baker.make_recipe("sms.failed_sms", municipality=None)
        try:
            sms_obj.status = SMSQueueStatus.PENDING
            sms_obj.save()
            self.fail("No exception raised. Expected Integrity Error")
        except IntegrityError:
            pass

    def test_managers(self):
        baker.make_recipe(
            "sms.pending_sms", municipality=self.municipality, _quantity=3
        )
        baker.make_recipe("sms.failed_sms", municipality=self.municipality, _quantity=4)
        baker.make_recipe("sms.sent_sms", municipality=self.municipality, _quantity=10)

        self.assertEqual(SMSQueueElement.ready.count(), 0)
        self.assertEqual(SMSQueueElement.failed.count(), 4)

        self.municipality.is_active = True
        self.municipality.save()

        self.assertEqual(SMSQueueElement.ready.count(), 3)
        self.assertEqual(SMSQueueElement.failed.count(), 4)


class SMSManagerTest(TestBase):
    def setUp(self):
        self.municipality = Municipality.objects.get(pk=get_random_municipality_id())

    def test_send_no_mun(self):
        SMSManager.send_sms("98234789", "What does Marsellus Wallace look like?")
        last = SMSQueueElement.objects.last()
        self.assertSent(last)
        self.assertEqual(last.phone_number, "98234789")
        self.assertEqual(last.content, "What does Marsellus Wallace look like?")
        self.assertIsNone(last.municipality)

        self.assertEqual(SMSQueueElement.objects.count(), 1)

    def test_send_with_mun_inactive(self):
        SMSManager.send_sms_with_municipality("98346789", "What", self.municipality)
        last = SMSQueueElement.objects.last()

        self.assertPending(last)
        self.assertEqual(last.phone_number, "98346789")
        self.assertEqual(last.content, "What")
        self.assertEqual(last.municipality, self.municipality)

        self.assertEqual(SMSQueueElement.objects.count(), 1)

    def test_send_with_mun_active(self):
        self.activate_municipality()

        SMSManager.send_sms_with_municipality(
            "34678931", "What country you from", self.municipality
        )
        last = SMSQueueElement.objects.last()

        self.assertSent(last)
        self.assertEqual(last.phone_number, "34678931")
        self.assertEqual(last.content, "What country you from")
        self.assertEqual(last.municipality, self.municipality)

        self.assertEqual(SMSQueueElement.objects.count(), 1)

    def test_send_with_mun_inactive_flush(self):
        SMSManager.send_sms_with_municipality(
            "68363478", "What, what", self.municipality
        )
        last = SMSQueueElement.objects.last()

        self.assertPending(last)
        self.assertEqual(last.phone_number, "68363478")
        self.assertEqual(last.content, "What, what")
        self.assertEqual(last.municipality, self.municipality)

        SMSManager.flush_pending(self.municipality)  # Not active, nothing happens
        last.refresh_from_db()
        self.assertPending(last)

        self.activate_municipality()
        SMSManager.flush_pending(self.municipality)  # Gets flushed
        last.refresh_from_db()
        self.assertSent(last)

        self.assertEqual(SMSQueueElement.objects.count(), 1)

    def test_send_no_mun_multiple(self):
        SMSManager.send_sms(
            ["98234789", "98234789"], "What does Marsellus Wallace look like?"
        )
        all_sms = SMSQueueElement.objects.all()
        for sms in all_sms:
            self.assertSent(sms)
            self.assertEqual(sms.phone_number, "98234789")
            self.assertEqual(sms.content, "What does Marsellus Wallace look like?")
            self.assertIsNone(sms.municipality)

        self.assertEqual(SMSQueueElement.objects.count(), 2)

    #######################################################################
    #                               Helpers                               #
    #######################################################################

    def activate_municipality(self):
        self.municipality.is_active = True
        self.municipality.save()

    def assertSent(self, sms: SMSQueueElement):
        self.assertEqual(sms.status, SMSQueueStatus.SENT)

    def assertPending(self, sms: SMSQueueElement):
        self.assertEqual(sms.status, SMSQueueStatus.PENDING)

    def assertFailed(self, sms: SMSQueueElement):
        self.assertEqual(sms.status, SMSQueueStatus.FAILED)
