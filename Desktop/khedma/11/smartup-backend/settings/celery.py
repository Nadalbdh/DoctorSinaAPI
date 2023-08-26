import os

from celery.schedules import crontab

from celery import Celery

# set the default Django settings module for the 'celery' program.
from settings.settings import BROKER_URL

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.settings")

app = Celery("settings", broker=BROKER_URL)

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


app.conf.beat_schedule = {
    "send_daily_email": {
        "task": "daily_email",
        "schedule": crontab(hour=7, minute=0, day_of_week="tue-fri"),
        "args": (24,),
    },
    "send_monday_email": {
        "task": "daily_email",
        "schedule": crontab(hour=7, minute=0, day_of_week="mon"),
        "args": (72,),
    },
    "send_daily_forum_email": {
        "task": "daily_forum_email",
        "schedule": crontab(hour=8, minute=0),
    },
    "send_daily_reminder": {
        "task": "daily_reminder_email",
        "schedule": crontab(hour=8, minute=0),
    },
    "send_weekly_reminder_email": {
        "task": "weekly_reminder_email",
        "schedule": crontab(hour=8, minute=0, day_of_week=1),
    },
    "send_q2w_reminder_email": {
        "task": "q2w_reminder_email",
        "schedule": crontab(hour=8, minute=0, day_of_month="1,15"),  # each 2 week
    },
    "flush_failed_sms": {
        "task": "flush_failed_sms",
        "schedule": crontab(minute=0),  # every hour
    },
    "operation_update_performance_table": {
        "task": "operation_update_performance_table",
        "schedule": crontab(day_of_month=1, hour=5),
    },
    "etickets_performance_table": {
        "task": "etickets_performance_table",
        "schedule": crontab(day_of_month=1, hour=5),
    },
    "delete_temporary_docx_and_xlsx_files": {
        "task": "delete_temporary_docx_and_xlsx_files",
        "schedule": crontab(hour=5),
        "args": (["**/media/subject-access-requests/files/", "**/media/internal/"],),
    },
}


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
