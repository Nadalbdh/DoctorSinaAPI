from typing import Iterable, Union

from celery.utils.log import get_task_logger

from settings.celery import app

from .handlers import handler
from .models import Notification

logger = get_task_logger(__name__)


@app.task(bind=False, name="send_push_notification")
def send_push_notification(identifiers: Union[Iterable[int], int]) -> None:
    if hasattr(identifiers, "__iter__"):
        notifications = Notification.objects.filter(pk__in=identifiers)
    else:
        notifications = [Notification.objects.get(pk=identifiers)]
    for notification in notifications:
        try:
            handler.handle_notification(notification)
        except:
            logger.error(
                f"failed pushing a notification about {notification.subject_type.model}"
            )
        else:
            notification.is_sent = True
            notification.save()
