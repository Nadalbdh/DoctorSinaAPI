import os

from backend.enum import SMSAPIType

from .base import BASE_DIR

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    },
}

SMS_GATEWAY_API_TYPE = SMSAPIType.Dev

DISABLE_LOGGING_MIDDLEWARE = True

DEBUG = True

CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
}
