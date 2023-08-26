import logging
from typing import Iterable, List, Union

import requests

from backend.enum import OsTypes
from backend.models import Municipality
from settings.settings import (
    ENV,
    ENVS,
    SMS_GATEWAY_API_KEY,
    SMS_GATEWAY_API_TYPE,
    SMS_GATEWAY_URL,
)
from sms.enum import SMSQueueStatus
from sms.models import SMSQueueElement

logger = logging.getLogger("default")


class SMSManager:
    headers = {"Authorization": "Api-Key {}".format(SMS_GATEWAY_API_KEY)}

    @staticmethod
    def send_sms(
        phone_number: Union[Iterable[str], str], sms_content: str, os=OsTypes.OTHER
    ):
        """
        Sends an sms without a municipality.
        """
        return SMSManager.send_sms_with_municipality(phone_number, sms_content, os=os)

    @staticmethod
    def send_sms_with_municipality(
        phone_number: Union[Iterable[str], str],
        sms_content: str,
        municipality: Municipality = None,
        os=OsTypes.OTHER,
    ):
        if isinstance(phone_number, str):
            return SMSManager.__send_sms_with_municipality(
                phone_number, sms_content, municipality, os
            )
        return [
            SMSManager.__send_sms_with_municipality(
                phone, sms_content, municipality, os
            )
            for phone in phone_number
        ]

    @staticmethod
    def __send_sms_with_municipality(
        phone_number: str,
        sms_content: str,
        municipality: Municipality = None,
        os=OsTypes.OTHER,
    ):
        """
        Sends an sms associated with a municipality. If the municipality is not active,
        a queue element is created.
        The functions returns an SMSQueueStatus.
        :return: the status of the sms.
        """
        # If the municipality is not provided or is inactive, don't send anything and pretend it went through
        if municipality is not None and not municipality.is_active:
            SMSQueueElement.objects.create(
                phone_number=phone_number,
                content=sms_content,
                municipality=municipality,
                status=SMSQueueStatus.PENDING,
                os=os,
            )
            return SMSQueueStatus.PENDING

        #  The API response
        request_status = SMSManager.__send_sms_request(phone_number, sms_content, os)
        status = SMSManager.__api_response__to_status(request_status)

        SMSQueueElement.objects.create(
            phone_number=phone_number,
            content=sms_content,
            municipality=municipality,
            status=status,
            os=os,
        )

        return status

    @staticmethod
    def flush_pending(municipality: Municipality = None) -> int:
        """
        Retries to send the pending SMSs, given the respective municipality
        is active. If a municipality parameter is given, only the SMSs corresponding
        to that municipality are flushed.
        The number of successfully sent SMSs is returned.
        :return: the number of sms sent.
        """
        sms_to_send = SMSQueueElement.ready.all()
        if municipality is not None:
            sms_to_send = sms_to_send.filter(municipality=municipality)
        return SMSManager.retry_multiple(sms_to_send)

    @staticmethod
    def flush_failed() -> int:
        """
        Retries to send the failed SMSs.
        The number of successfully sent SMSs is returned.
        :return: the number of sms sent.
        """
        return SMSManager.retry_multiple(SMSQueueElement.failed.all())

    @staticmethod
    def retry_sending(sms: SMSQueueElement):
        """
        Retries to send the SMSQueueElement. Returns its new status.
        :return: the status of the sms
        """
        status_code = SMSManager.__send_sms_request(
            sms.phone_number, sms.content, sms.os
        )
        sms.status = SMSManager.__api_response__to_status(status_code)
        sms.save()
        return sms.status

    @staticmethod
    def retry_multiple(sms_collection: List[SMSQueueElement]) -> int:
        """
        Retries to send the collection of SMS given.
        The number of successfully sent SMSs is returned.
        """
        status_collection = [SMSManager.retry_sending(sms) for sms in sms_collection]
        return len([s for s in status_collection if s == SMSQueueStatus.SENT])

    @staticmethod
    def __send_sms_request(phone_number: str, sms_content: str, os=OsTypes.OTHER):
        if ENV != ENVS.PROD:
            logger.info("SMS sent to %s:%s", phone_number, sms_content)
            return 0
        try:
            data = {
                "phone_number": phone_number,
                "body": sms_content,
                "os": os,
                "api": SMS_GATEWAY_API_TYPE,
            }
            res = requests.post(
                SMS_GATEWAY_URL + "send_sms", headers=SMSManager.headers, json=data
            )
            if res.status_code == 200:
                return 0
            if res.status_code == 429:  # Too many requests
                return 1
            logger.warning(
                "Couldn't send sms through SMS Gateway status code: %s", res.status_code
            )
            return 2
        except Exception as e:  # pylint: disable=broad-except
            logger.exception("SMS Gateway is unreachable %s", e)
            return -1

    @staticmethod
    def __api_response__to_status(api_response: int):
        """
        Converts the code returned by the SMS API to an SMSQueueStatus.
        Note: PENDING cannot be returned; since an attempt have been made.
        """
        if api_response == 0:
            return SMSQueueStatus.SENT
        if api_response == 1:
            return SMSQueueStatus.TOO_MANY_ATTEMPTS
        return SMSQueueStatus.FAILED

    @staticmethod
    def broadcast_sms(phone_numbers: list, sms_content: str):
        for phone_number in phone_numbers:
            SMSManager.send_sms(phone_number, sms_content)
