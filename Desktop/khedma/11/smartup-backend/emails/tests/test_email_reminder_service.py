from datetime import timedelta

from django.core import mail
from django.utils import timezone
from model_bakery import baker

from backend.enum import MunicipalityPermissions, RequestStatus
from backend.helpers import ManagerHelpers
from backend.models import Municipality
from backend.tests.baker import bake_updatable_full_time
from backend.tests.test_base import TestBase
from backend.tests.test_utils import fake, get_random_municipality_id, set_and_save_date
from emails.services.reminder_emails_service import ReminderEmailHandler


class TestDailyEmail(TestBase):
    def setUp(self):
        self.municipality = Municipality.objects.get(pk=get_random_municipality_id())
        self.today = timezone.now()
        self.__bake_managers()
        self.__bake_complaints()
        self.__bake_subjects_accesses()

    def test_send_daily_object_mails(self):
        self.__bake_dossiers()  # i call it here because there is another test depends on dossiers (no interference)
        ReminderEmailHandler(municipality=self.municipality).send_daily_reminder()
        self.assertEqual(2, len(mail.outbox[0].to))  # managers complaints number
        self.assertEqual(len(mail.outbox), 19)

        """complaint received reminder"""
        self.assertIn("تذكير أول بورود تشكيات", mail.outbox[0].subject)
        self.assertIn("3 أيام", mail.outbox[0].body)

        self.assertIn("تذكير ثاني بورود لمشكل", mail.outbox[1].subject)
        self.assertIn("10 أيام", mail.outbox[1].body)

        self.assertIn("تذكير نهائي بورود لمشكل", mail.outbox[2].subject)
        self.assertIn("17 يوم", mail.outbox[2].body)

        """complaint process reminder"""
        self.assertIn("تذكير أول بتحيين للمشكل", mail.outbox[3].subject)
        self.assertIn("7 أيام", mail.outbox[3].body)

        self.assertIn("تذكير ثاني بتحيين للمشكل", mail.outbox[4].subject)
        self.assertIn("21 يوم", mail.outbox[4].body)

        self.assertIn("تذكير ثالث بتحيين للمشكل", mail.outbox[5].subject)
        self.assertIn("49 يوم", mail.outbox[5].body)

        self.assertIn("تذكير رابع بتحيين للمشكل", mail.outbox[6].subject)
        self.assertIn("97 يوم", mail.outbox[6].body)

        self.assertIn("تذكير خامس بتحيين للمشكل", mail.outbox[7].subject)
        self.assertIn("193 يوم", mail.outbox[7].body)

        self.assertIn("تذكير نهائي بتحيين للمشكل", mail.outbox[8].subject)
        self.assertIn("385 يوم", mail.outbox[8].body)

        """subject_access received reminder"""
        self.assertIn("تذكير أول بورود مطلب نفاذ إلى المعلومة", mail.outbox[9].subject)
        self.assertIn("2 أيام", mail.outbox[9].body)

        self.assertIn(
            "تذكير ثاني بورود مطلب نفاذ إلى المعلومة", mail.outbox[11].subject
        )
        self.assertIn("8 أيام", mail.outbox[11].body)

        self.assertIn(
            "تذكير ثالث بورود مطلب نفاذ إلى المعلومة", mail.outbox[12].subject
        )
        self.assertIn("14 يوم", mail.outbox[12].body)

        self.assertIn(
            "تذكير نهائي بورود مطلب نفاذ إلى المعلومة", mail.outbox[13].subject
        )
        self.assertIn("20 يوم", mail.outbox[13].body)

        """dossier process reminder"""

        self.assertIn("تذكير أول بتحديث وضعية مطلب الرخصة", mail.outbox[14].subject)
        self.assertIn("14 يوم", mail.outbox[14].body)

        self.assertIn("تذكير ثاني بتحديث وضعية مطلب الرخصة", mail.outbox[15].subject)
        self.assertIn("28 يوم", mail.outbox[15].body)

        self.assertIn("تذكير ثالث بتحديث وضعية مطلب الرخصة", mail.outbox[16].subject)
        self.assertIn("42 يوم", mail.outbox[16].body)

        self.assertIn("تذكير رابع بتحديث وضعية مطلب الرخصة", mail.outbox[17].subject)
        self.assertIn("56 يوم", mail.outbox[17].body)

        self.assertIn("تذكير نهائي بتحديث وضعية مطلب الرخصة", mail.outbox[18].subject)
        self.assertIn("84 يوم", mail.outbox[18].body)

    def test_no_weekly_email(self):
        self.__bake_news(self.today - timedelta(5))
        self.__bake_news(self.today - timedelta(6))
        ReminderEmailHandler(municipality=self.municipality).send_weekly_reminder()
        self.assertEqual(len(mail.outbox), 0)

    def test_send_weekly_email(self):
        self.__bake_news(self.today - timedelta(15))
        self.__bake_news(self.today - timedelta(28))
        self.__bake_news(self.today - timedelta(51))
        ReminderEmailHandler(municipality=self.municipality).send_weekly_reminder()
        self.assertEqual(1, len(mail.outbox))
        self.assertEqual(1, len(mail.outbox[0].to))  # managers news number
        self.assertIn("تذكير بإضافة المستجدات البلدية", mail.outbox[0].subject)
        self.assertIn("لآخر 14 يوم", mail.outbox[0].subject)
        self.assertIn("14 يوم", mail.outbox[0].body)

    def test_no_q2w_email(self):
        self.__bake_event(self.today - timedelta(13))
        self.__bake_event(self.today - timedelta(8))
        self.__bake_report(self.today - timedelta(21))  # interval 28 days
        self.__bake_dossier(self.today - timedelta(7))
        self.__bake_dossier(self.today - timedelta(13))
        ReminderEmailHandler(municipality=self.municipality).send_q2w_reminder()
        self.assertEqual(len(mail.outbox), 0)

    def test_send_event_q2w_email(self):
        self.__bake_event(self.today - timedelta(32))  # this
        self.__bake_event(self.today - timedelta(43))
        self.__bake_event(self.today - timedelta(51))
        self.__bake_report(self.today - timedelta(32))  # this
        self.__bake_report(self.today - timedelta(43))
        self.__bake_report(self.today - timedelta(51))
        self.__bake_dossier(self.today - timedelta(32))  # this
        self.__bake_dossier(self.today - timedelta(43))
        self.__bake_dossier(self.today - timedelta(51))
        ReminderEmailHandler(municipality=self.municipality).send_q2w_reminder()
        self.assertEqual(3, len(mail.outbox))
        self.assertEqual(2, len(mail.outbox[0].to))  # managers event number
        self.assertEqual(1, len(mail.outbox[1].to))  # managers report number
        self.assertEqual(1, len(mail.outbox[2].to))  # managers dossier number

        self.assertIn("تذكير بإضافة المواعيد البلدية", mail.outbox[0].subject)
        self.assertIn("طيلة آخر 28 يوم", mail.outbox[0].subject)
        self.assertIn("28 يوم", mail.outbox[0].body)

        self.assertIn(
            "تذكير بإضافة  تقارير اجتماعات اللجان لبلدية", mail.outbox[1].subject
        )
        self.assertIn("آخر 28 يوم", mail.outbox[1].subject)
        self.assertIn("28 يوم", mail.outbox[1].body)

        self.assertIn(
            "تذكير بإضافة مطالب الرخص البلدية المستجدة", mail.outbox[2].subject
        )
        self.assertIn("آخر 28 يوم", mail.outbox[2].subject)
        self.assertIn("28 يوم", mail.outbox[2].body)

    def __bake_managers(self):
        self.__bake_manager([MunicipalityPermissions.MANAGE_COMPLAINTS])
        self.__bake_manager([MunicipalityPermissions.MANAGE_COMPLAINTS])
        self.__bake_manager([MunicipalityPermissions.MANAGE_DOSSIERS])
        self.__bake_manager([MunicipalityPermissions.MANAGE_REPORTS])
        self.__bake_manager([MunicipalityPermissions.MANAGE_EVENTS])
        self.__bake_manager([MunicipalityPermissions.MANAGE_EVENTS])
        self.__bake_manager([MunicipalityPermissions.MANAGE_NEWS])
        self.__bake_manager([MunicipalityPermissions.MANAGE_SUBJECT_ACCESS_REQUESTS])

    def __bake_complaints(self):
        """
        Updated: Sending one mail for each configuration  ( anti spam )
        """
        # received complaints
        self.__bake_complaint(self.today - timedelta(1))
        self.__bake_complaint(self.today - timedelta(2))
        self.__bake_complaint(self.today - timedelta(3))  # this
        self.__bake_complaint(self.today - timedelta(3))  # this
        self.__bake_complaint(self.today - timedelta(4))
        self.__bake_complaint(self.today - timedelta(4))
        self.__bake_complaint(self.today - timedelta(4))
        self.__bake_complaint(self.today - timedelta(11))
        self.__bake_complaint(self.today - timedelta(11))
        self.__bake_complaint(self.today - timedelta(10))  # this
        self.__bake_complaint(self.today - timedelta(16))
        self.__bake_complaint(self.today - timedelta(16))
        self.__bake_complaint(self.today - timedelta(17))  # this
        # process complaints
        self.__bake_complaint_processing(self.today - timedelta(5))
        self.__bake_complaint_processing(self.today - timedelta(5))
        self.__bake_complaint_processing(self.today - timedelta(7))  # this
        self.__bake_complaint_processing(self.today - timedelta(8))
        self.__bake_complaint_processing(self.today - timedelta(8))
        self.__bake_complaint_processing(self.today - timedelta(21))  # this
        self.__bake_complaint_processing(self.today - timedelta(49))  # this
        self.__bake_complaint_processing(self.today - timedelta(97))  # this
        self.__bake_complaint_processing(self.today - timedelta(193))  # this
        self.__bake_complaint_processing(self.today - timedelta(385))  # this

    def __bake_dossiers(self):
        self.__bake_dossier_processing(self.today - timedelta(5))
        self.__bake_dossier_processing(self.today - timedelta(6))
        self.__bake_dossier_processing(self.today - timedelta(7))
        self.__bake_dossier_processing(self.today - timedelta(8))
        self.__bake_dossier_processing(self.today - timedelta(8))
        self.__bake_dossier_processing(self.today - timedelta(13))
        self.__bake_dossier_processing(self.today - timedelta(14))  # this
        self.__bake_dossier_processing(self.today - timedelta(15))
        self.__bake_dossier_processing(self.today - timedelta(28))  # this
        self.__bake_dossier_processing(self.today - timedelta(42))  # this
        self.__bake_dossier_processing(self.today - timedelta(50))
        self.__bake_dossier_processing(self.today - timedelta(56))  # this
        self.__bake_dossier_processing(self.today - timedelta(84))  # this

    def __bake_subjects_accesses(self):
        # received subject access
        self.__bake_subject_access_request(self.today - timedelta(2))  # this
        self.__bake_subject_access_request(self.today - timedelta(4))
        self.__bake_subject_access_request(self.today - timedelta(8))  # this
        self.__bake_subject_access_request(self.today - timedelta(8))  # this
        self.__bake_subject_access_request(self.today - timedelta(14))  # this
        self.__bake_subject_access_request(self.today - timedelta(15))
        self.__bake_subject_access_request(self.today - timedelta(16))
        self.__bake_subject_access_request(self.today - timedelta(20))  # this
        self.__bake_subject_access_request(self.today - timedelta(21))

    def __bake_subject_access_request(self, created_at):
        return set_and_save_date(
            baker.make(
                "backend.subjectaccessrequest", municipality_id=self.municipality.id
            ),
            str(created_at),
        )

    def __bake_complaint(self, created_at):
        return set_and_save_date(
            baker.make("backend.complaint", municipality_id=self.municipality.id),
            str(created_at),
        )

    def __bake_dossier(self, created_at):
        return set_and_save_date(
            baker.make("backend.dossier", municipality_id=self.municipality.id),
            str(created_at),
        )

    def __bake_report(self, created_at):
        return set_and_save_date(
            baker.make("backend.report", municipality_id=self.municipality.id),
            str(created_at),
        )

    def __bake_news(self, created_at):
        return set_and_save_date(
            baker.make("backend.news", municipality_id=self.municipality.id),
            str(created_at),
            "published_at",
        )

    def __bake_event(self, ending_at):
        return set_and_save_date(
            baker.make("backend.event", municipality_id=self.municipality.id),
            str(ending_at.date()),
            "ending_date",
        )

    def __bake_complaint_processing(self, created_at):
        return bake_updatable_full_time(
            "backend.complaint",
            str(created_at - timedelta(hours=1)),
            # logic of creation before update status that why the minus 1 hours
            RequestStatus.PROCESSING,
            str(created_at),
            self.municipality,
        )

    def __bake_dossier_processing(self, created_at):
        return bake_updatable_full_time(
            "backend.dossier",
            str(created_at - timedelta(hours=1)),
            # logic of creation before update status that why the minus 1 hours
            RequestStatus.PROCESSING,
            str(created_at),
            self.municipality,
        )

    def __set_interval(self, days):
        start_day = self.today - timedelta(days=days + 1) + timedelta(hours=1)
        end_day = start_day + timedelta(days=1)
        return (start_day, end_day)

    def __bake_manager(self, permissions, email=fake.email()):
        manager = baker.make(
            "backend.manager", municipality_id=self.municipality.id, user__email=email
        )
        ManagerHelpers(manager, self.municipality).assign_permissions(permissions)
        return manager
