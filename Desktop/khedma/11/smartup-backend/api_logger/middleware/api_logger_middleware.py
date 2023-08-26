import json
import time

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.urls import resolve

from api_logger.start_logger_when_server_starts import logger_thread
from api_logger.utils import get_client_ip, mask_sensitive_data

DRF_API_LOGGER_SKIP_URL_NAME = {
    "static-texts": ["GET"],
    "static-text": ["GET"],
}
MEDIA_PATH = "/media/"


class APILoggerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        namespace = resolve(request.path).namespace
        url_name = resolve(request.path).url_name

        if MEDIA_PATH in request.path or (
            url_name in DRF_API_LOGGER_SKIP_URL_NAME
            and request.method in DRF_API_LOGGER_SKIP_URL_NAME[url_name]
        ):
            return self.get_response(request)
        if settings.DISABLE_LOGGING_MIDDLEWARE or namespace == "admin":
            return self.get_response(request)

        start_time = time.time()
        request_data = ""
        try:
            request_data = json.loads(request.body) if request.body else ""
        except json.JSONDecodeError:
            request_data = dict(request.POST)
        except Exception:
            request_data = "Request body isn't of type json/form-data"

        response = self.get_response(request)
        execution_time = time.time() - start_time
        user = request.user
        if isinstance(request.user, AnonymousUser):
            user = None

        method = request.method
        api_url = request.get_full_path()
        data = dict(
            api_url=api_url,
            user=user,
            body=mask_sensitive_data(request_data),
            method=method,
            client_ip=get_client_ip(request),
            status_code=response.status_code,
            execution_time=execution_time,
        )

        if logger_thread:
            logger_thread.put_log_data(data=data)
        return response
