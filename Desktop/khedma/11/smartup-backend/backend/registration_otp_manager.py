import logging
from random import randint

from django.contrib.auth.models import User
from django.core.cache import cache

from backend.enum import CachePrefixes
from sms.enum import SMSQueueStatus
from utils.SMSManager import SMSManager

logger = logging.getLogger("default")
MAX_OTP_RETRIES = 10


# TODO Comment this code: specify return values


def add_otp(phone_number, otp):
    otps = cache.get("{}:{}".format(CachePrefixes.REGISTER, phone_number))
    if otps is None:
        otps = []
    if len(otps) >= MAX_OTP_RETRIES:
        return False
    otps.append(otp)
    cache.set("{}:{}".format(CachePrefixes.REGISTER, phone_number), otps, 7200)
    return True


def prepare_registration_otp(user: User):
    # TODO Use enumerations instead of integers
    otp = str(randint(100000, 999999))
    if not add_otp(user.get_username(), otp):
        return SMSQueueStatus.TOO_MANY_ATTEMPTS
    logger.info("Your elBaladiya.tn code is: %s", otp)
    # FIXME REMOVE THIS
    logger.debug("Setting OTP for %s = %s", user.get_username(), otp)
    citizen = user.citizen
    # TODO This is useless, let's remove it
    citizen.validation_code = otp
    citizen.save()
    return SMSManager.send_sms(
        user.get_username(),
        "{} est le code de confirmation de votre compte elBaladiya.tn.".format(otp),
    )


def check_registration_otp(phone_number, otp):
    correct_otps = cache.get("{}:{}".format(CachePrefixes.REGISTER, phone_number))
    if correct_otps is None:
        return False
    logger.debug(
        "Reading OTP for %s = %s, received: %s. equal = %s",
        phone_number,
        correct_otps,
        otp,
        otp in correct_otps,
    )
    return otp in correct_otps


def check_registration_otp_v2(phone_number, otp):
    user = User.objects.get(username=phone_number)
    try:
        correct_otps = [user.citizen.validation_code]
        if not correct_otps:
            return False
        logger.debug(
            "Reading OTP for %s = %s, received: %s. equal = %s",
            phone_number,
            correct_otps,
            otp,
            otp in correct_otps,
        )
        return otp in correct_otps
    except:
        # TODO(low priority): add more exception handling here
        return False
