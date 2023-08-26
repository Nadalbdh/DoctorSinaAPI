import logging

from pyfcm import FCMNotification

from settings.settings import FCM_API_KEY

push_service = FCMNotification(api_key=FCM_API_KEY)
logger = logging.getLogger("default")


def send_single_notification(notification):
    device = notification.get_user_last_device()
    if device is None:
        return None
    if not device.fcm_token:
        return None
    try:
        result = push_service.single_device_data_message(
            registration_id=device.fcm_token,
            data_message={
                "title": notification.title,
                "body": notification.body,
                "subject_type": notification.subject_type.model,
                "subject_id": notification.subject_id,
                "action_param": notification.action_param,
                "action_type": notification.action_type,
                "municipality_name_fr": notification.subject_object.municipality.name_fr
                if hasattr(notification.subject_object, "municipality")
                else None,
            },
        )
        return result
    except Exception as errors:
        logger.error("%s ", errors)


def send_notifications(notifications):
    for notification in notifications:
        send_single_notification(notification)
