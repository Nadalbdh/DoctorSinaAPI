from datetime import timedelta

from django.core import mail
from django.utils import timezone
from model_bakery import baker

from backend.enum import MunicipalityPermissions
from backend.helpers import ManagerHelpers
from backend.models import Municipality
from backend.tests.test_base import TestBase
from backend.tests.test_utils import fake, get_random_municipality_id, set_and_save_date
from emails.services.daily_emails_service import (
    DailyComplaintEmail,
    DailySubjectAccessRequestEmail,
)

one_day = timedelta(days=1)
two_days = timedelta(days=2)
four_days = timedelta(days=4)

WEEKDAY = 24
WEEKEND = 72


class TestDailyEmail(TestBase):
    def setUp(self):
        self.municipality = Municipality.objects.get(pk=get_random_municipality_id())
        self.today = timezone.now()
        self.__bake_managers()
        self.__bake_complaints()
        self.__bake_subjects_access_requests()

    def test_send_daily_complaint_email_weekday(self):
        DailyComplaintEmail(self.municipality, WEEKDAY).send()
        self.assertGreater(len(mail.outbox), 0)
        self.assertEqual(2, len(mail.outbox[0].to))  # complaints managers
        self.assertIn("تبليغ عن المشكل", mail.outbox[0].body)

    def test_send_daily_subject_access_email_weekday(self):
        DailySubjectAccessRequestEmail(self.municipality, WEEKDAY).send()
        self.assertGreater(len(mail.outbox), 0)
        self.assertEqual(1, len(mail.outbox[0].to))  # sar managers
        self.assertIn("مطلبين نفاذ للمعلومة", mail.outbox[0].body)

    def test_send_daily_complaint_email_weekend(self):
        DailyComplaintEmail(self.municipality, WEEKEND).send()
        self.assertIn("3   تبليغات عن المشاكل", mail.outbox[0].body)

    def test_send_daily_subject_access_email_weekend(self):
        DailySubjectAccessRequestEmail(self.municipality, WEEKEND).send()
        self.assertIn("4  مطالب نفاذ للمعلومة", mail.outbox[0].body)

    def test_no_new_objects(self):
        DailyComplaintEmail(self.municipality, 0).send()
        DailySubjectAccessRequestEmail(self.municipality, 0).send()
        self.assertEqual(len(mail.outbox), 0)

    def __bake_managers(self):
        self.__bake_manager([MunicipalityPermissions.MANAGE_COMPLAINTS])
        self.__bake_manager([MunicipalityPermissions.MANAGE_COMPLAINTS])
        self.__bake_manager([MunicipalityPermissions.MANAGE_DOSSIERS])
        self.__bake_manager([MunicipalityPermissions.MANAGE_SUBJECT_ACCESS_REQUESTS])

    def __bake_complaints(self):
        self.__bake_complaint(self.today - one_day)  # WeekDay + Weekend
        self.__bake_complaint(self.today - two_days)  # Weekend
        self.__bake_complaint(self.today - two_days)  # Weekend
        self.__bake_complaint(self.today - four_days)
        self.__bake_complaint(self.today - four_days)
        self.__bake_complaint(self.today - four_days)

    def __bake_subjects_access_requests(self):
        self.__bake_subject_access_request(self.today - one_day)  # WeekDay + Weekend
        self.__bake_subject_access_request(self.today - one_day)  # WeekDay + Weekend
        self.__bake_subject_access_request(self.today - two_days)  # Weekend
        self.__bake_subject_access_request(self.today - two_days)  # Weekend
        self.__bake_subject_access_request(self.today - four_days)

    def __bake_complaint(self, created_at):
        return set_and_save_date(
            baker.make("backend.complaint", municipality_id=self.municipality.id),
            str(created_at),
        )

    def __bake_subject_access_request(self, created_at):
        return set_and_save_date(
            baker.make(
                "backend.subjectaccessrequest", municipality_id=self.municipality.id
            ),
            str(created_at),
        )

    def __bake_manager(self, permissions):
        manager = baker.make(
            "backend.manager",
            municipality_id=self.municipality.id,
            user__email=fake.email(),
        )
        ManagerHelpers(manager, self.municipality).assign_permissions(permissions)
        return manager
