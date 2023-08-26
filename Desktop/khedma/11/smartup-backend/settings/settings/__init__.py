import bugsnag
from decouple import config

from .base import *


class ENVS:
    PROD = "PROD"
    STAGING = "STAGING"
    TEST = "TEST"  # for pipeline
    DEV = "DEV"  # for local development


ENV = config("ENV", default=ENVS.TEST)

BUGSNAG = {
    "api_key": config("BUGSNAG_API_KEY", default=""),
}

if ENV in [ENVS.DEV, ENVS.TEST]:  # Disable bugsnag on local instances
    bugsnag.before_notify(lambda _: False)

if ENV == ENVS.PROD:
    from .production import *
elif ENV == ENVS.STAGING:
    from .staging import *
elif ENV == ENVS.DEV:
    from .development import *
else:
    from .test import *
