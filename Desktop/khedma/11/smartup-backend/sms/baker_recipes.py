from model_bakery.recipe import Recipe

from backend.enum import OsTypes
from backend.tests.test_utils import get_db_choices, random_stream
from sms.enum import SMSQueueStatus
from sms.models import SMSQueueElement

sms_recipe = Recipe(
    SMSQueueElement,
    status=random_stream(get_db_choices(SMSQueueStatus)),
    os=random_stream(get_db_choices(OsTypes)),
)

pending_sms = sms_recipe.extend(status=SMSQueueStatus.PENDING)
failed_sms = sms_recipe.extend(status=SMSQueueStatus.FAILED)
sent_sms = sms_recipe.extend(status=SMSQueueStatus.SENT)
