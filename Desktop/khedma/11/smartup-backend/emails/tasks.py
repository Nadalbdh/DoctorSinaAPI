from celery.utils.log import get_task_logger

from backend.models import Municipality
from emails.services.daily_emails_service import (
    DailyComplaintEmail,
    DailyForumEMail,
    DailySubjectAccessRequestEmail,
)
from emails.services.reminder_emails_service import ReminderEmailHandler
from emails.services.weekly_emails_service import WeeklyEMailService
from settings.celery import app
from settings.cron_healthcheck import LoggingTask

logger = get_task_logger(__name__)


@app.task(bind=True)
def send_weekly_email_task(self):
    WeeklyEMailService.send_weekly_email()


@app.task(bind=True, base=LoggingTask, name="daily_email")
def send_daily_email(self, for_past_x_hours=24):
    """
    Daily emails contain summary of last 24 hours for each day/ last 72 hours on monday
    """
    for municipality in Municipality.objects.active():
        try:
            DailySubjectAccessRequestEmail(municipality, for_past_x_hours).send()
            DailyComplaintEmail(municipality, for_past_x_hours).send()
        except Exception as e:
            logger.error(f"send_daily_email {municipality.id}, {e}")


@app.task(base=LoggingTask, name="daily_forum_email")
def send_daily_forum_email():
    for municipality in Municipality.objects.active():
        DailyForumEMail(municipality).send()


@app.task(bind=True, base=LoggingTask, name="daily_reminder_email")
def send_daily_reminder_email(self):
    """
    Daily reminder emails contain complaints & subjects accesses whose status has not been changed for a while
    """
    for municipality in Municipality.objects.active():
        try:
            ReminderEmailHandler(municipality=municipality).send_daily_reminder()
        except Exception as e:
            logger.error(f"send_daily_reminder_email {municipality.id}, {e}")


@app.task(bind=True, base=LoggingTask, name="weekly_reminder_email")
def send_weekly_reminder_email(self):
    """
    Weekly reminder emails
    """
    for municipality in Municipality.objects.active():
        try:
            ReminderEmailHandler(municipality=municipality).send_weekly_reminder()
        except Exception as e:
            logger.error(f"send_weekly_reminder_email {municipality.id}, {e}")


@app.task(bind=True, base=LoggingTask, name="q2w_reminder_email")
def send_q2w_reminder_email(self):
    """
    Reminder emails for events each 2 weeks
    """
    for municipality in Municipality.objects.active():
        try:
            ReminderEmailHandler(municipality=municipality).send_q2w_reminder()
        except Exception as e:
            logger.error(f"q2w_reminder_email {municipality.id}, {e}")
