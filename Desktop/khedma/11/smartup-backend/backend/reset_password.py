import logging
import random

from django.core.cache import cache
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken

from backend.enum import CachePrefixes, ResetPasswordTypes
from utils.SMSManager import SMSManager

logger = logging.getLogger("default")


# TODO: set up mail config
def prepare_reset_password_otp(user, phone_number, type):
    otp = str(random.randint(100000, 999999))
    content = (
        "{} est le code de reinitialisation de votre compte elBaladiya.tn.".format(otp)
    )
    cache.set("{}:{}".format(CachePrefixes.RESET, phone_number), otp, 7200)
    logger.info(content)
    if type == ResetPasswordTypes.SMS:
        return SMSManager.send_sms(phone_number, content)
    elif type == ResetPasswordTypes.EMAIL:
        return send_mail(
            "Votre code de reinitialisation de mot de passe elBaladiya.tn",
            content,
            "elBaladiyatn@gmail.com",
            [user.email],
            fail_silently=False,
        )


def check_reset_password_otp(phone_number, otp):
    correct_otp = cache.get("{}:{}".format(CachePrefixes.RESET, phone_number))
    return correct_otp == otp


def generate_jwt_token(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
