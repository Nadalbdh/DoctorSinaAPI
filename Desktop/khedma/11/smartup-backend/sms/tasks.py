from celery.utils.log import get_task_logger

from backend.models import Municipality
from settings.celery import app
from settings.cron_healthcheck import LoggingTask
from sms.sms_manager import SMSManager

logger = get_task_logger(__name__)


@app.task(base=LoggingTask, name="flush_failed_sms")
def flush_failed_sms():
    try:
        SMSManager.flush_failed()
    except Exception as e:
        logger.error(f"flush_failed_sms, {e}")


@app.task(base=LoggingTask, name="flush_pending_sms")
def flush_pending_sms(municipality_id: int):
    try:
        municipality = Municipality.objects.get(pk=municipality_id)
        SMSManager.flush_pending(municipality)
    except Exception as e:
        logger.error(f"flush_pending_sms {municipality.id}, {e}")
