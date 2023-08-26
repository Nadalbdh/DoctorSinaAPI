import logging

from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver

from backend.enum import DossierTypes, MunicipalityPermissions, RequestStatus
from backend.functions import is_manager
from backend.models import (
    Comment,
    Complaint,
    Dossier,
    Event,
    OperationUpdate,
    SubjectAccessRequest,
)

from .enums import NotificationActionTypes
from .functions import notify_managers_for
from .models import NotifiableModel, Notification
from .tasks import send_push_notification

logger = logging.getLogger("default")


@receiver(post_save, sender=Notification, dispatch_uid="push_notification_on_creation")
def push_notification_on_creation(sender, instance, created, **kwargs):
    if created:
        send_push_notification.delay(instance.id)


@receiver(post_save, sender=Dossier, dispatch_uid="push-notify-managers-dossier")
def push_notify_managers_for_dossier(sender, instance, created, **kwargs):
    if not created or is_manager(instance.created_by):
        return
    notify_managers_for(
        MunicipalityPermissions.MANAGE_DOSSIERS,
        municipality=instance.municipality,
        title="تم اظافة مطلب جديد",
        body=DossierTypes.translate(instance.type),
        subject_type=ContentType.objects.get_for_model(Dossier),
        subject_object=instance,
        action_type=NotificationActionTypes.OPEN_SUBJECT,
    )


@receiver(
    post_save,
    sender=SubjectAccessRequest,
    dispatch_uid="push-notify-managers-subject-access",
)
def push_notify_managers_for_subject_access(sender, instance, created, **kwargs):
    if not created:
        return
    notify_managers_for(
        MunicipalityPermissions.MANAGE_SUBJECT_ACCESS_REQUESTS,
        municipality=instance.municipality,
        title="تم اظافة مطلب نفاذ إلى المعلومة",
        body=f"مطلب للوثيقة: {instance.document}",
        subject_type=ContentType.objects.get_for_model(SubjectAccessRequest),
        subject_object=instance,
        action_type=NotificationActionTypes.OPEN_SUBJECT,
    )


@receiver(post_save, sender=Comment, dispatch_uid="push-notify-managers-comment")
def push_notify_managers_for_comment(sender, instance, created, **kwargs):
    if not created or is_manager(instance.created_by):
        return
    notify_managers_for(
        MunicipalityPermissions.MANAGE_FORUM,
        municipality=instance.municipality,
        title="تم اظافة تعليق",
        body=f"بعنوان: {instance.title}",
        subject_type=ContentType.objects.get_for_model(Comment),
        subject_object=instance,
        action_type=NotificationActionTypes.OPEN_SUBJECT,
    )


@receiver(post_save, sender=Complaint, dispatch_uid="push-notify-managers-complaint")
def push_notify_managers_for_complaint(sender, instance, created, **kwargs):
    if not created:
        return
    notify_managers_for(
        MunicipalityPermissions.MANAGE_COMPLAINTS,
        municipality=instance.municipality,
        title="تم اظافة تشكي",
        body=f"{instance.problem[:20]}",
        subject_type=ContentType.objects.get_for_model(Complaint),
        subject_object=instance,
        action_type=NotificationActionTypes.OPEN_SUBJECT,
    )


@receiver(
    post_save, sender=OperationUpdate, dispatch_uid="push-notify-followers-on-update"
)
def push_notify_followers_on_update(sender, instance, created, **kwargs):
    """
    Sends an sms to the user whenever a new update is created
    """
    if not created or instance.status == RequestStatus.RECEIVED:
        return
    # Get the correct subject, depending on the type of the operation
    subject = {
        # TODO Bring me python 3.10 with pattern matching and I'll change this.
        "dossier": lambda: f"المطلب البلدي الخاص بيك عدد {instance.operation.unique_identifier}",
        "subject access request": lambda: f"مطلب النفاذ الخاص بيك “{instance.operation.document[:8]}..”",
        "complaint": lambda: f" التشكي الخاص بيك “{instance.operation.problem[:8]}..”",
        "comment": lambda: f" المقترح الخاص بيك “{instance.operation.title[:8]}..”",
        "reservation": lambda: "",
    }[instance.content_type.name]()

    body = f"""تم تحيين وضعية {subject} يمكن تصفح التحديثات عبر حسابك في elBaladiya.tn الرابط: {instance.operation.citizen_url}"""

    if hasattr(instance.operation, "followers"):
        notifications = []
        for user in instance.operation.followers.all():
            notifications.append(
                Notification(
                    user=user,
                    title=instance.operation.municipality.name,
                    body=body,
                    subject_type=ContentType.objects.get_for_model(OperationUpdate),
                    subject_object=instance,
                    action_type=NotificationActionTypes.OPEN_SUBJECT,
                    municipality=instance.operation.municipality,
                )
            )
        Notification.objects.bulk_create(notifications)


@receiver(post_save, sender=Event)
def send_notification_event_created(sender, instance, created, **kwargs):
    """
    Notifies the citizen of municipality when an event has been created
    """
    title = f"تم إضافة موعد"
    body = f"تم إضافة موعد لبلدية {instance.municipality.name} بعنوان { instance.title[:50]}"
    notifications = [
        Notification(
            user=citizen.user,
            title=title,
            body=body,
            subject_type=ContentType.objects.get_for_model(Event),
            subject_object=instance,
            action_type=NotificationActionTypes.OPEN_SUBJECT,
            municipality=instance.municipality,
        )
        for citizen in instance.municipality.citizens.all()
    ]

    Notification.objects.bulk_create(notifications)


@receiver(post_save, sender=OperationUpdate)
def push_notification_operation_update(sender, instance, created, **kwargs):
    if (
        created
        and isinstance(instance.operation, NotifiableModel)
        and instance.status == RequestStatus.RECEIVED
    ):
        users = instance.operation.get_notifiable_users()
        body = instance.operation.get_notification_body()
        notifications = [
            Notification(
                user=user,
                title=instance.operation.notification_title,
                body=body,
                subject_type=ContentType.objects.get_for_model(instance.operation),
                subject_object=instance,
                action_type=NotificationActionTypes.OPEN_SUBJECT,
                municipality=instance.operation.municipality,
            )
            for user in users
        ]
        Notification.objects.bulk_create(notifications)
