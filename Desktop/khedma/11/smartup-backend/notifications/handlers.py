import logging
from typing import Iterable

from pyfcm import FCMNotification

from backend.enum import OsTypes
from backend.models import RegisteredDevice
from notifications import models
from settings.settings import ENV, ENVS, FCM_API_KEY

logger = logging.getLogger("default")


class NotificationHandler:
    def handle_notification(self, notification: models.Notification) -> None:
        pass

    def handle_notifications(
        self, notifications: Iterable[models.Notification]
    ) -> None:
        for notification in notifications:
            self.handle_notification(notification)


class LoggerNotificationHandler(NotificationHandler):
    def handle_notification(self, notification: models.Notification) -> None:
        logger.info("Sending notification %s", notification)


class FCMPushNotificationHandler(NotificationHandler):
    push_service = FCMNotification(api_key=FCM_API_KEY)

    def handle_notification(self, notification: models.Notification) -> None:
        device: RegisteredDevice = notification.get_user_last_device()

        if device is None:
            return

        try:
            logger.info(f"Sending notification {notification}")
            self.push_service.single_device_data_message(
                registration_id=device.fcm_token,
                data_message={
                    "title": notification.title,
                    "body": notification.body,
                    "subject_type": notification.subject_type.model,
                    "subject_id": notification.subject_id,
                    "action_param": notification.action_param,
                    "action_type": notification.action_type,
                    # TODO mobile package name
                    "click_action": "https://elbaladiya.tn"
                    if device.os == OsTypes.OTHER
                    else "https://elbaladiya.tn",
                    "municipality_name_fr": notification.subject_object.municipality.name_fr
                    if hasattr(notification.subject_object, "municipality")
                    else None,
                },
                content_available=True,
                extra_notification_kwargs={
                    "image": "https://elbaladiya.tn/assets/images/login/logo_with_slogan_white.png",
                    "color": "#2b8dff",
                },
            )
        except Exception as exc:
            raise exc


handler: NotificationHandler = (
    FCMPushNotificationHandler()
    if ENV in [ENVS.PROD, ENVS.STAGING]
    else LoggerNotificationHandler()
)
