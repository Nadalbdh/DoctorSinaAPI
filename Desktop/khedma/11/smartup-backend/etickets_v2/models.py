import uuid
from datetime import date, datetime
from typing import List

import requests
import rules
from django.contrib.auth.models import User
from django.db import models
from django.db.models import F, Q
from rules.contrib.models import RulesModelBase, RulesModelMixin

from backend.models import Municipality
from backend.rules import is_manager, rules
from settings.settings import ETICKETS_RESET_HOUR


class RemoteServerActions(models.Model):
    """models that have equivalents on the remote backend or can perform actions/requests to it"""

    def post(self, *args, **kwargs) -> requests.Response:
        return requests.post(*args, **kwargs)

    class Meta:
        abstract = True


class ValidReservationManager(models.Manager):
    """Manager for retrieving valid reservations"""

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                ticket_num__gte=F("service__current_ticket"),
                created_at__date=date.today(),
            )
        )

    use_in_migrations = True


class NoLongerValidReservationManager(models.Manager):
    """Manager for retrieving no longer valid reservations"""

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                Q(ticket_num__lt=F("service__current_ticket"))
                | Q(is_active=False)
                | Q(created_at__date__lt=date.today())
            )
        )

    use_in_migrations = True


class Agency(RulesModelMixin, models.Model, metaclass=RulesModelBase):
    """
    an agency is basically a sub-municipality
    A.K.A: دائرة بلدية
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True)
    local_ip = models.CharField(max_length=40, null=True, blank=True, unique=True)
    secured_connection = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    latitude = models.DecimalField(max_digits=10, default=36.797423, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, default=10.165894, decimal_places=7)
    # relations
    municipality = models.ForeignKey(
        Municipality, on_delete=models.CASCADE, related_name="local_agencies"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    # weekday <required>
    weekday_first_start = models.TimeField()
    weekday_first_end = models.TimeField()
    weekday_second_start = models.TimeField()
    weekday_second_end = models.TimeField()
    # saturday <optional>
    saturday_first_start = models.TimeField(null=True, blank=True)
    saturday_first_end = models.TimeField(null=True, blank=True)
    saturday_second_start = models.TimeField(null=True, blank=True)
    saturday_second_end = models.TimeField(null=True, blank=True)

    # metadata
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "agencies"
        verbose_name = "agency"
        ordering = [
            "-created_at",
        ]
        rules_permissions = {
            "change": is_manager,
            "add": is_manager,
            "view": rules.always_allow,
            "delete": is_manager,
        }

    def to_simplified_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "local_ip": self.get_ip(),
        }

    def get_ip(self):
        return self.local_ip

    def is_prefix_used(self, prefix):
        return self.services.filter(name__startswith=prefix + "-").exists()

    def is_existing_name(self, name):
        return self.services.filter(name__endswith=name).exists()


class Service(RulesModelMixin, RemoteServerActions, metaclass=RulesModelBase):
    """
    a service provided by a (municipality/ agency) , eg: الحالة المدنية
    """

    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    is_active = models.BooleanField(default=False)
    last_booked_ticket = models.IntegerField(blank=True, null=True)
    current_ticket = models.IntegerField(default=0, blank=False, null=False)
    avg_time_per_person = models.IntegerField(default=8, blank=False, null=False)
    # relations
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    agency = models.ForeignKey(
        Agency, on_delete=models.CASCADE, related_name="services"
    )

    # metadata
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = [
            "-name",
        ]
        rules_permissions = {
            "change": is_manager,
            "add": is_manager,
            "view": rules.always_allow,
            "delete": is_manager,
        }

    def to_simplified_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "last_booked_ticket": self.last_booked_ticket,
            "current_ticket": self.current_ticket,
            "avg_time_per_person": self.avg_time_per_person,
            "created_at": self.created_at,
        }

    def reset_counter_to_zero(self):
        """reset current_ticket and last_booked_ticket if TIME is in ETICKETS_RESET_HOUR"""
        if datetime.now().hour <= ETICKETS_RESET_HOUR:
            self.current_ticket = 0
            self.last_booked_ticket = None
            self.save()

    def get_people_waiting(self) -> int:
        """
        Return the number of people waiting in row
        """
        if self.last_booked_ticket is not None:
            result = (
                self.last_booked_ticket
                - self.current_ticket
                - Reservation.valid_objects.filter(
                    service__pk=self.id,
                    is_active=False,
                ).count()
            )
            return result if result > 0 else 0
        return 0

    def create_booking_locally(self):
        """creates a booking for a given service in agency"""
        protocol = "https" if self.agency.secured_connection else "http"
        url = f"{protocol}://{self.agency.local_ip}/api/services/{self.id}/book/"
        headers = {"Content-type": "application/json"}
        return self.post(url, json={}, headers=headers)


class Reservation(RemoteServerActions):
    """
    A model to represent a reservation made by a user.
    """

    ticket_num = models.IntegerField(blank=False, null=False)
    # relations
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="reservations"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="etickets_v2_reservations"
    )  # TODO: rename after deprication eticket app

    # metadata
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_physical = models.BooleanField(default=False)

    objects = models.Manager()
    valid_objects = ValidReservationManager()
    no_longer_valid_objects = NoLongerValidReservationManager()

    def __str__(self):
        return f"ticket number: {self.ticket_num}"

    def notification_content(self) -> List[str]:
        """arabic text needed no notify a citizen that their reservation is coming up"""
        difference = self.get_people_ahead(ignore_current=True)
        if difference == 0:
            return (
                f"يرجى التقدم إلى النافذة لتلقي الخدمة :{self.service.name}",
                f"{self.service.agency.municipality.name}",
            )
        if difference == 1:
            return (
                f"أمامك شخص واحد في صف خدمة {self.service.name}",
                f"{self.service.agency.municipality.name}",
            )
        if difference == 2:
            return (
                f"أمامك شخصان في صف خدمة {self.service.name}",
                f"{self.service.agency.municipality.name}",
            )
        return (
            f"أمامك {difference} أشخاص  في صف خدمة {self.service.name}",
            f"{self.service.agency.municipality.name}",
        )

    def get_people_ahead(self, ignore_current=False) -> int:
        """
        Calculate the number of people ahead of the current person holding the
        reservation in the queue.
        """
        canceled_reservations_ahead = Reservation.no_longer_valid_objects.filter(
            ticket_num__gt=self.ticket_num
        ).count()
        actual_count = (
            self.ticket_num - self.service.current_ticket - canceled_reservations_ahead
        )
        returned_count = actual_count - 1 if ignore_current else (actual_count)
        return returned_count if returned_count > 0 else 0

    def cancel_locally(self):
        """send the id_service and cancelled id_reservation to local server"""
        protocol = "https" if self.service.agency.secured_connection else "http"
        url = f"{protocol}://{self.service.agency.local_ip}/api/services/{self.service.id}/cancel-ticket/"
        headers = {"Content-type": "application/json"}
        data = {"ticket_num": self.ticket_num}
        return self.post(url, json=data, headers=headers)
