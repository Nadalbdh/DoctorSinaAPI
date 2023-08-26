import logging

from django.db.utils import IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from backend.exceptions import CustomError

logger = logging.getLogger("default")


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    logger.error(exc)
    if isinstance(exc, CustomError):
        data = {"details": exc.ERROR_MESSAGE}
        return Response(data, status=exc.ERROR_STATUS)

    if isinstance(exc, IntegrityError):
        data = {"details": str(exc)}
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    # returns response as handled normally by the framework
    return response
