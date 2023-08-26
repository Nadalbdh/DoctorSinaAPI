from django.core.mail import send_mail
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from backend.enum import RequestStatus
from backend.exceptions import InconsistentCategoriesError, InconsistentRegionError
from backend.models import (
    Complaint,
    ComplaintCategory,
    Dossier,
    OperationUpdate,
    SMSBroadcastRequest,
)
from settings.settings import EMAIL_HOST_USER
from utils.SMSManager import SMSManager


@receiver(post_save, sender=Dossier)
def send_sms_dossier_created(sender, instance, created, **kwargs):
    """
    Notifies the user when the dossier is created
    """
    if not created or not instance.phone_number:
        return
    body = f""" يمكنك متابعة حالة مطلب "{instance.get_type_display()}" الخاص بك عبر منصة البلدية الرقمية {instance.citizen_url}
    الرقم الوحيد للمطلب : {instance.unique_identifier}
    بلدية {instance.municipality.name}."""
    SMSManager.send_sms(instance.phone_number, body)


@receiver(post_save, sender=OperationUpdate, dispatch_uid="sms-notify-update")
def sms_notify_update(sender, instance, created, **kwargs):
    """
    Sends an sms to the user whenever a new update is created
    """
    if (
        not created
        or instance.status == RequestStatus.RECEIVED
        or instance.operation.contact_number is None
    ):
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

    body = f"""تم تحيين وضعية {subject} يمكن تصفح التحديثات عبر حسابك في elBaladiya.tn
الرابط: {instance.operation.citizen_url}"""

    SMSManager.send_sms(instance.operation.contact_number, body)


@receiver(
    post_save, sender=SMSBroadcastRequest, dispatch_uid="new_sms_broadcast_request"
)
def send_sms_broadcast_request_mail(sender, instance, created, **kwargs):
    if not created:
        return
    subject = "SMS Broadcast request"
    body = f"""
        A New SMS Broadcast received:
        Municipality:{str(instance.municipality)}
        Created By:{str(instance.created_by)}
        Text:{instance.text}
        Target:{instance.target}
        Quantity:{instance.get_quantity()}
        Scheduled on:{instance.scheduled_on}
        """
    send_mail(subject, body, EMAIL_HOST_USER, [EMAIL_HOST_USER], fail_silently=True)


@receiver(pre_save, sender=Complaint, dispatch_uid="validate_complaint")
def validate_complaint(sender, instance, **kwargs):
    # Validating categories
    if not instance.pk and instance.category is None:
        default, _ = ComplaintCategory.objects.get_or_create(name="تشكيات متنوعة")
        instance.category = default

    if (
        instance.sub_category is not None
        and instance.sub_category.category != instance.category
    ):
        raise InconsistentCategoriesError()
    # Validating regions
    if (
        instance.region is not None
        and instance.region.municipality_id != instance.municipality_id
    ):
        raise InconsistentRegionError()
