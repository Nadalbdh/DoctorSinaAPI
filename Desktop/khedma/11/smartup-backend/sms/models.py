from django.db import models

from backend.enum import OsTypes
from backend.models import Municipality
from sms.enum import SMSQueueStatus


class SMSQueueReadyManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(status=SMSQueueStatus.PENDING, municipality__is_active=True)
        )


class SMSQueueFailedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=SMSQueueStatus.FAILED)


class SMSQueueElement(models.Model):
    # Needed for sending the sms
    phone_number = models.CharField(max_length=8)
    content = models.TextField()
    os = models.CharField(choices=OsTypes.get_choices(), max_length=16)
    # Needed for the queue and for logging
    municipality = models.ForeignKey(
        Municipality, on_delete=models.SET_NULL, related_name="sms", null=True
    )
    status = models.CharField(choices=SMSQueueStatus.get_choices(), max_length=50)

    objects = models.Manager()  # default manager
    ready = SMSQueueReadyManager()
    failed = SMSQueueFailedManager()

    class Meta:
        constraints = [
            models.CheckConstraint(
                #  If a municipality is none, then the status can't be PENDING
                check=~models.Q(
                    municipality__isnull=True, status=SMSQueueStatus.PENDING
                ),
                name="mun_null_implies_not_pending",
            )
        ]
