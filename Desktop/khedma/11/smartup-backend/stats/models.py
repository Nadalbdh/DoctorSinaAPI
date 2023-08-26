from django.db import models
from django.db.models import Model

from backend.models import Municipality
from etickets_v2.models import Agency


class OperationUpdatePerformance(Model):
    municipality = models.ForeignKey(
        Municipality, on_delete=models.CASCADE, related_name="performance"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    average_first_response_days = models.FloatField(null=True, blank=True)

    # each attribute is supposed to reflect a key from an enum backend.enum.RequestStatus
    # should store % of each operation updates status
    received_percentage = models.FloatField(default=0)
    processing_percentage = models.FloatField(default=0)
    accepted_percentage = models.FloatField(default=0)
    rejected_percentage = models.FloatField(default=0)
    not_clear_percentage = models.FloatField(default=0)
    invalid_percentage = models.FloatField(default=0)


class EticketsPerformance(Model):
    agency = models.ForeignKey(
        Agency, on_delete=models.CASCADE, related_name="etickets_performance"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    physical_reservation_percentage = models.FloatField(default=0)
    digital_reservation_percentage = models.FloatField(default=0)
    not_digitized_reservation_percentage = models.FloatField(default=0)

    push_notifications_sent = models.FloatField(default=0)
