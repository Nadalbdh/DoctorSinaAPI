import glob
import logging
import os
from datetime import date, timedelta

from celery.utils.log import get_task_logger

from backend.enum import SMSBroadcastRequestTarget
from backend.models import Citizen, SMSBroadcastRequest
from settings.celery import app
from settings.cron_healthcheck import LoggingTask
from utils.SMSManager import SMSManager

logger = get_task_logger(__name__)
logger.setLevel(logging.INFO)


@app.task
def broadcast_sms(request_id):
    sms_request = SMSBroadcastRequest.objects.get(id=request_id)

    if not sms_request.is_approved():
        logger.warning(
            "SMS Broadcasts should be approved before being sent: id=%d", sms_request.id
        )
        return

    # Start the process
    logger.info("Stated broadcasting SMSs: id=%d", sms_request.id)
    sms_request.set_status_sending()

    # Get targeted phones numbers

    phone_numbers = None

    if sms_request.target == SMSBroadcastRequestTarget.CUSTOM:
        phone_numbers = sms_request.phone_numbers.values_list("number", flat=True)
    else:
        target = None
        if sms_request.target == SMSBroadcastRequestTarget.FOLLOWING_CITIZENS:
            target = sms_request.municipality.citizens.all()
        if sms_request.target == SMSBroadcastRequestTarget.REGISTERED_CITIZENS:
            target = sms_request.municipality.starred_citizens.all()
        if sms_request.target == SMSBroadcastRequestTarget.ALL_CITIZENS:
            target = Citizen.objects.all()
        if sms_request.target == SMSBroadcastRequestTarget.INACTIVE_CITIZENS:
            if sms_request.number_of_days is None:
                target = Citizen.objects.filter(user__is_active=False)
            else:
                start_parsing_date = date.today() - timedelta(
                    days=sms_request.number_of_days
                )
                target = Citizen.objects.filter(
                    user__is_active=False, user__date_joined__gte=start_parsing_date
                )
        phone_numbers = target.values_list("user__username", flat=True)

    # Broadcast SMSs
    SMSManager.broadcast_sms(phone_numbers, sms_request.text)

    if not sms_request.is_created_by_staff():
        # Update SMS credit + total SMS consumption
        municipality = sms_request.municipality
        municipality.sms_credit -= sms_request.get_quantity()
        municipality.total_sms_consumption += sms_request.get_quantity()

        municipality.save()

    # Finish the process
    sms_request.set_status_sent()
    logger.info("Finished broadcasting SMSs: id=%d", sms_request.id)


@app.task(base=LoggingTask, name="delete_temporary_docx_and_xlsx_files")
def delete_temporary_docx_and_xlsx_files(self, directories_to_clean=[]):
    """
    delete temporary docx and xlsx files
    any file in the directories_to_clean matching *.docx
    """
    for directory in directories_to_clean:
        files_matching = glob.glob(
            os.path.join(directory, "*.docx"), os.path.join(directory, "*.xlsx")
        )
        for file_path in files_matching:
            try:
                os.remove(file_path)
            except OSError:
                logger.error(f"Error while deleting {file_path}")
