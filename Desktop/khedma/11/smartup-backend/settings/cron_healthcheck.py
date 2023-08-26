import json
import logging
from datetime import datetime

import requests

from celery import Task
from settings.settings import ENV, ENVS, ERROR_CHANNEL, INFO_CHANNEL

logger = logging.getLogger("default")


def send_notification_to_teams(data, CHANNEL: str) -> None:
    HEADERS = {"Content-Type": "application/json"}
    response = requests.post(CHANNEL, headers=HEADERS, data=json.dumps(data))
    if response.status_code == 200:
        logger.info("Notification sent successfully to dev team.")


class LoggingTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        message = f"Task '{self.name}' finished successfully on {datetime.now().strftime('%H:%M:%S')}"
        if ENV == ENVS.PROD:
            send_notification_to_teams(
                {
                    "@type": "MessageCard",
                    "@context": "http://schema.org/extensions",
                    "themeColor": "0078D7",
                    "title": message,
                    "summary": f"Success on task_id {task_id}",
                },
                INFO_CHANNEL,
            )
        logger.info(message)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        message = f"Task '{self.name}' failed on {datetime.now().strftime('%H:%M:%S')}. Error: {exc}"
        if ENV == ENVS.PROD:
            send_notification_to_teams(
                {
                    "@type": "MessageCard",
                    "@context": "http://schema.org/extensions",
                    "themeColor": "ed2626",
                    "title": message,
                    "summary": f"Failure on task_id {task_id}",
                },
                ERROR_CHANNEL,
            )
        logger.error(message)

    def __call__(self, *args, **kwargs):
        try:
            return super().__call__(*args, **kwargs)
        except Exception as exc:
            logger.error(f"Task '{self.name}' raised an exception on Error: {exc}")
            raise exc
