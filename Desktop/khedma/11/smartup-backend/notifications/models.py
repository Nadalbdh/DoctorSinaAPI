from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from .enums import NotificationActionTypes


class NotificationManager(models.Manager):
    def objects(self):
        return self.get_queryset()

    def bulk_create(self, objs, *args, **kwargs):
        from .tasks import send_push_notification

        super().bulk_create(objs, *args, **kwargs)
        # since bulk_create doesn't fire signals
        ids = [i.id for i in objs]
        send_push_notification.apply_async(args=(ids,), countdown=25)


class Notification(models.Model):
    # managers
    objects = NotificationManager()

    # fields
    user = models.ForeignKey(
        User, related_name="notifications", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    subject_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, blank=True, null=True
    )
    subject_id = models.PositiveIntegerField(blank=True, null=True)
    subject_object = GenericForeignKey("subject_type", "subject_id")
    action_param = models.CharField(default="", max_length=255)
    action_type = models.CharField(
        choices=NotificationActionTypes.get_choices(),
        max_length=30,
        default=NotificationActionTypes.OPEN_SUBJECT,
    )
    municipality = models.ForeignKey(
        "backend.Municipality",
        on_delete=models.SET_NULL,
        related_name="notifications",
        null=True,
    )

    class Meta:
        ordering = ["-created_at"]
        db_table = "backend_notification"
        # TODO add constraints (if action_type == open_object => subject_id and subject_type should be not null)

    def __str__(self):
        return "Notification {} {} ".format(self.pk, self.title)

    def mark_as_read(self):
        self.is_read = True
        self.save()

    def get_user_last_device(self):
        return self.user.devices.order_by("-last_login").first()


class NotifiableModel(models.Model):
    class Meta:
        abstract = True

    notification_title = None

    def get_notification_body(self):
        raise NotImplementedError(f"get_notification_body in {self.__class__.__name__}")

    def get_notifiable_users(self):
        raise NotImplementedError(f"get_notifiable_users in {self.__class__.__name__}")
