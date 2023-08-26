import datetime
from datetime import timedelta

from django.utils import timezone

from backend.enum import MunicipalityPermissions
from backend.models import Dossier, Event, News, Report
from emails.services import OneObjectEMailService
from emails.services.mixins import PermissionBasedRecipientsMixin
from settings.settings import DOSSIER_URL, EVENTS_URL, NEWS_URL, REPORT_URL


class IntervalBasedEmailService(PermissionBasedRecipientsMixin, OneObjectEMailService):
    """
    Sends an email to remind officers of adding objects.
    This class handles the logic and requires its children
    to implement 'get_last_date', returning the date of
    the last added model.
    """

    base_url = None

    def __init__(self, municipality, interval):
        self.municipality = municipality
        self.interval = interval
        self.today = timezone.now()

    def get_template_params(self, mobj):
        return {
            "municipality": self.municipality,
            "base_url": self.base_url,
            "nb_days": mobj,
        }

    def get_last_date(self):
        """
        The date of the last object added
        """
        raise ValueError("This needs to be implemented")

    def get_mail_object(self):
        """
        The mail_object is determined from the last object added
        """
        last_date = self.get_last_date()
        interval = timedelta(days=self.interval)
        if isinstance(last_date, datetime.datetime):
            # There are models having DateTimeField and others having DateField
            last_date = last_date.date()
        duration_since_last = self.today.date() - last_date
        return (duration_since_last // interval) * self.interval


class ReminderEventEmail(IntervalBasedEmailService):
    template = "email_events_reminder_template.html"
    base_url = EVENTS_URL
    permission = MunicipalityPermissions.MANAGE_EVENTS

    def get_subject(self, mobj):
        return f"تذكير بإضافة المواعيد البلدية {self.municipality.name} طيلة آخر {mobj} يوم"

    def get_last_date(self):
        """
        Fetch Latest Event based on ending_date
        """
        return (
            Event.objects.filter(municipality=self.municipality)
            .latest("ending_date")
            .ending_date
        )


class ReminderNewsEmail(IntervalBasedEmailService):
    template = "email_news_reminder_template.html"
    base_url = NEWS_URL
    permission = MunicipalityPermissions.MANAGE_NEWS

    def get_subject(self, mobj):
        if mobj > 10:
            return f"تذكير بإضافة المستجدات البلدية {self.municipality.name} لآخر {mobj} يوم"
        return (
            f"تذكير بإضافة المستجدات البلدية {self.municipality.name} لآخر {mobj} أيام"
        )

    def get_last_date(self):
        """
        Fetch Latest News based on published_at
        """
        return (
            News.objects.filter(municipality=self.municipality)
            .latest("published_at")
            .published_at
        )


class ReminderReportEmail(IntervalBasedEmailService):
    template = "email_report_reminder_template.html"
    base_url = REPORT_URL
    permission = MunicipalityPermissions.MANAGE_REPORTS

    def get_subject(self, mobj):
        return f"تذكير بإضافة  تقارير اجتماعات اللجان لبلدية {self.municipality.name} المنقضية آخر {mobj} يوم"

    def get_last_date(self):
        """
        Fetch latest Report based on created_at
        """
        return (
            Report.objects.filter(municipality=self.municipality)
            .latest("created_at")
            .created_at
        )


class ReminderDossierEmail(IntervalBasedEmailService):
    template = "email_dossier_reminder_template.html"
    base_url = DOSSIER_URL
    permission = MunicipalityPermissions.MANAGE_DOSSIERS

    def get_subject(self, mobj):
        return f"تذكير بإضافة مطالب الرخص البلدية المستجدة آخر {mobj} يوم ل{self.municipality.name}"

    def get_last_date(self):
        """
        Fetch Latest Dossier based on created_at
        """

        return (
            Dossier.objects.filter(municipality=self.municipality)
            .latest("created_at")
            .created_at
        )
