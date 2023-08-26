import os
import sys
from datetime import timedelta
from pathlib import Path

from decouple import config

from utils import cast_dict, cast_list

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("SECRET_KEY")

METABASE_SITE_URL = config("METABASE_SITE_URL", default="http://metabase.elbaladiya.tn")
METABASE_SECRET_KEY = config("METABASE_SECRET_KEY", default="SHHH")

ALLOWED_HOSTS = ["*"]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "rest_framework",
    "drf_spectacular",
    "corsheaders",
    "guardian",
    "django_extensions",
    "django_cleanup",
    "django_celery_beat",
    "django_celery_results",
    "macros",
    "import_export",
    "rules.apps.AutodiscoverRulesConfig",
    "rest_framework_api_key",
    # Internal apps
    "backend",
    "emails",
    "polls",
    "sms",
    "reports",
    "etickets",  # with express display (denden)
    "etickets_v2",  # with our local servers
    "notifications",
    "stats",
    "api_logger",
]

SITE_ID = 1
MIDDLEWARE = [
    "bugsnag.django.middleware.BugsnagMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "backend.middlewares.LogEverythingMiddleware",
    "backend.middlewares.LogAdminMiddleware",
    "api_logger.middleware.api_logger_middleware.APILoggerMiddleware",
]

CORS_ORIGIN_ALLOW_ALL = True
ROOT_URLCONF = "settings.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "templates"),
            os.path.join(BASE_DIR, "backend", "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[%(levelname)s][%(asctime)s][File %(pathname)s:%(lineno)d]: %(message)s",
            "datefmt": "%d-%m-%Y %H:%M:%S",
        },
        "standard": {
            "format": "[%(levelname)s][%(asctime)s] %(message)s",
            "datefmt": "%d-%m-%Y %H:%M:%S",
        },
    },
    "handlers": {
        "log_everything_handler": {
            "level": "DEBUG",
            "maxBytes": 1024 * 1024 * 100,  # 100 MB Total
            "class": "logging.handlers.RotatingFileHandler",
            "backupCount": 1,
            "filename": "logs/everything.log",
            "formatter": "standard",
        },
        "admin_panel_handler": {
            "level": "ERROR",
            "maxBytes": 1024 * 1024 * 100,  # 100 MB Total
            "class": "logging.handlers.RotatingFileHandler",
            "backupCount": 1,
            "filename": "logs/admin_panel.log",
            "formatter": "standard",
        },
        "debugging": {
            "level": "DEBUG",
            "maxBytes": 1024 * 1024 * 100,  # 100 MB Total
            "class": "logging.handlers.RotatingFileHandler",
            "backupCount": 5,
            "filename": "logs/debug/debug.log",
            "formatter": "verbose",
        },
        "info": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "logs/info.log",
            "formatter": "standard",
        },
        "warnings": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": "logs/warning.log",
            "formatter": "verbose",
        },
        "errors": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": "logs/error.log",
            "formatter": "verbose",
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "standard",
        },
        "bugsnag": {
            "level": "WARNING",
            "class": "bugsnag.handlers.BugsnagHandler",
        },
    },
    "loggers": {
        "default": {
            "handlers": [
                "console",
                "debugging",
                "info",
                "warnings",
                "errors",
                "bugsnag",
            ],
            "level": "DEBUG",
            "propagate": True,
        },
        "everything_logger": {
            "handlers": ["log_everything_handler"],
            "level": "DEBUG",
            "propagate": True,
        },
        "admin_logger": {
            "handlers": ["admin_panel_handler"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}
WSGI_APPLICATION = "settings.wsgi.application"

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 1},
    },
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.BCryptPasswordHasher",
]

AUTHENTICATION_BACKENDS = (
    "rules.permissions.ObjectPermissionBackend",
    "django.contrib.auth.backends.ModelBackend",  # default
    "guardian.backends.ObjectPermissionBackend",
)
LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["settings.custom_permissions.DefaultPermission"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "backend.exception_handler.custom_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "backend.pagination.CustomPagination",
    "PAGE_SIZE": 10,
}
SPECTACULAR_SETTINGS = {
    "TITLE": "elBaladiya.tn",
    "DESCRIPTION": "Backend API Documentation",
    "VERSION": "1.0.0",
}

DJANGO_ADMIN_URL = "management/admin"

SWAGGER_SETTINGS = {
    "LOGIN_URL": "/" + DJANGO_ADMIN_URL + "login",
    "LOGOUT_URL": "/" + DJANGO_ADMIN_URL + "logout",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(weeks=521),  # 10 years
}


ETICKET_SIGNATURE_SEGMENT_LENGTH = config(
    "ETICKET_SIGNATURE_SEGMENT_LENGTH", default=3, cast=int
)
ETICKET_SIGNATURE_SEGMENTS_COUNT = config(
    "ETICKET_SIGNATURE_SEGMENTS_COUNT", default=2, cast=int
)


ERROR_CHANNEL = config(
    "ERROR_CHANNEL",
    default="https://touneslina.webhook.office.com/webhookb2/aa254ce5-d8c4-46a0-b6c8-d69624d44ef3@5504ed12-c1eb-48f1-bc79-8e702a9c1587/IncomingWebhook/80c12aa3f4204fca81739f85cb765d66/84676316-5691-4d87-b07a-bbb71f229fae",
)
INFO_CHANNEL = config(
    "INFO_CHANNEL",
    default="https://touneslina.webhook.office.com/webhookb2/aa254ce5-d8c4-46a0-b6c8-d69624d44ef3@5504ed12-c1eb-48f1-bc79-8e702a9c1587/IncomingWebhook/3ca83f19661f4da9ad113b7b270123f8/84676316-5691-4d87-b07a-bbb71f229fae",
)

SMS_GATEWAY_URL = config("SMS_GATEWAY_URL", "")
SMS_GATEWAY_API_KEY = config("SMS_GATEWAY_API_KEY", "")

# General configuration
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", default="587")
EMAIL_USE_TLS = True

# Per address configuration
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD_DEFAULT", None)
EMAIL_HOST_USER = config("EMAIL_HOST_USER_DEFAULT", None)
EMAIL_CONFIG = {
    "notifications": config("EMAIL_HOST_CONFIG_NOTIFICATIONS", None, cast=cast_dict),
    "statistics": config("EMAIL_HOST_CONFIG_STATISTICS", None, cast=cast_dict),
}
EMAIL_BCC = config("EMAIL_BCC", ["contact@elbaladiya"], cast=cast_list)

FCM_API_KEY = config("FCM_API_KEY", default="FCM KEY")

BROKER_URL = config("BROKER_URL", default="redis://redis:6379/0")
CACHE_URL = config("CACHE_URL", default="redis://redis:6379/1")
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default=BROKER_URL)

TEST_RUNNER = "settings.test_runner.NoLoggingTestRunner"
TEST_OUTPUT_FILE_NAME = "report.xml"

BACK_OFFICE_URL = config("BACK_OFFICE_URL", default="idara.elbaladiya.tn")
FRONTEND_URL = config("FRONTEND_URL", default="elbaladiya.tn")
BACKEND_URL = config("BACKEND_URL", default="https://backend.elbaladiya.tn")

COMPLAINT_URL = BACK_OFFICE_URL + "/pages/complaints/edit/"
SUBJECT_ACCESS_REQUEST_URL = BACK_OFFICE_URL + "/pages/subject-access-requests/edit/"
NEWS_URL = BACK_OFFICE_URL + "/pages/news/edit/"
EVENTS_URL = BACK_OFFICE_URL + "/pages/events/edit/"
DOSSIER_URL = BACK_OFFICE_URL + "/pages/dossiers/edit/"
REPORT_URL = BACK_OFFICE_URL + "/pages/reports/edit/"

FILE_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024  # 20MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024  # 20MB

MAX_NB_TICKETS_PER_DAY_FOR_USER = config(
    "MAX_NB_TICKETS_PER_DAY_FOR_USER", default=10, cast=int
)

ETICKETS_RESET_HOUR = config("ETICKETS_RESET_HOUR", default=8, cast=int)

# Default queue size 50
DRF_LOGGER_INTERVAL = 10
# Default DB insertion interval is 10 seconds.
DRF_LOGGER_QUEUE_MAX_SIZE = 50

DOCX_TEMPLATES_PATH = "backend/templates/docs"

# Should be disabled in tests, because saving is asynchronous
DISABLE_LOGGING_MIDDLEWARE = config(
    "DISABLE_LOGGING_MIDDLEWARE", default=False, cast=bool
)
