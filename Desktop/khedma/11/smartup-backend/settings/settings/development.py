from decouple import config

from backend.enum import SMSAPIType

from .base import CACHE_URL

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST"),
        "PORT": config("DB_PORT"),
        "ATOMIC_REQUESTS": True,
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": CACHE_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
}

METABASE_SITE_URL = config(
    "METABASE_SITE_URL", default="http://dev-metabase.elbaladiya.tn"
)

SMS_GATEWAY_API_TYPE = SMSAPIType.Dev
BACKEND_URL = config("BACKEND_URL", default="https://dev-backend.elbaladiya.tn")

DEBUG = True
