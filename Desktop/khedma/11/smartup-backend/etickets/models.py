from django.contrib.auth.models import User
from django.db import models
from django.db.models import CASCADE

from backend.models import Municipality


class AgencyManager(models.Manager):
    def active(self):
        return self.get_queryset().filter(is_active=True)


class Agency(models.Model):
    name = models.CharField(max_length=150)
    municipality = models.ForeignKey(
        Municipality, on_delete=CASCADE, related_name="agencies"
    )
    # base endpoint for agency server
    base_url = models.URLField()
    authentication_user = models.CharField(max_length=50)
    authentication_password = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    num_agency = models.CharField(max_length=150)
    # weekday required
    weekday_first_start = models.TimeField()
    weekday_first_end = models.TimeField()
    weekday_second_start = models.TimeField()
    weekday_second_end = models.TimeField()
    # saturday optional
    saturday_first_start = models.TimeField(null=True, blank=True)
    saturday_first_end = models.TimeField(null=True, blank=True)
    saturday_second_start = models.TimeField(null=True, blank=True)
    saturday_second_end = models.TimeField(null=True, blank=True)

    objects = AgencyManager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Agencies"


class Reservation(models.Model):
    agency = models.ForeignKey(Agency, on_delete=CASCADE, related_name="reservations")
    created_by = models.ForeignKey(User, on_delete=CASCADE)
    service_name = models.CharField(max_length=150)
    service_id = models.IntegerField()
    ticket_info = models.TextField(blank=True, null=True)
    # Fields used to send notification to users
    ticket_num = models.IntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{}: {} - {}".format(
            self.service_name, self.agency, self.created_by.get_full_name()
        )
