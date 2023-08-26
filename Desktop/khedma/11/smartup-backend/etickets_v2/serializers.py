from datetime import date

from rest_framework import serializers

from backend.enum import TransporationMethods
from etickets_v2.helpers import are_none, check_valid_time
from etickets_v2.models import Agency, Reservation, Service
from settings.settings import (
    ETICKET_SIGNATURE_SEGMENT_LENGTH,
    ETICKET_SIGNATURE_SEGMENTS_COUNT,
)


class ServiceSerializer(serializers.ModelSerializer):
    """
    serializer for Service model, returns all fields along with
    the number of people waiting in the queue.
    """

    people_waiting = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Service
        fields = "__all__"

    @staticmethod
    def get_people_waiting(obj):
        """
        Return the number of people waiting in row
        """
        return obj.get_people_waiting()


class AgencySerializer(serializers.ModelSerializer):
    """
    serializer for Agency model, returns all fields along with whether it is open or not,
    has an e-ticket system or not, and the name of the municipality it belongs to.
    """

    is_open = serializers.SerializerMethodField(read_only=True)
    has_eticket = serializers.SerializerMethodField(read_only=True)
    municipality_name = serializers.SerializerMethodField(read_only=True)

    def validate(self, data):
        """
        Check that the start is before the stop.
        """
        dates = [
            ("weekday_first_start", "weekday_first_end"),
            ("weekday_second_start", "weekday_second_end"),
            ("saturday_first_start", "saturday_first_end"),
            ("saturday_second_start", "saturday_second_end"),
        ]

        for timespan in dates:
            if timespan[0] in data:
                if (
                    not are_none([data[timespan[0]], data[timespan[1]]])
                    and data[timespan[0]] > data[timespan[1]]
                ):
                    raise serializers.ValidationError(
                        {"message": f"{timespan[1]} is not a valid end time."}
                    )
        return data

    class Meta:
        model = Agency
        fields = "__all__"

    @staticmethod
    def get_is_open(obj):
        """
        Returns whether the Agency is open or not.
        Currently always returns True.
        """
        return True
        if check_valid_time(agency=obj, serializer=True):
            return True
        return False

    @staticmethod
    def get_has_eticket(obj):
        """
        Returns whether the Agency has an e-ticket system or not.
        """
        return isinstance(obj.get_ip(), str)

    @staticmethod
    def get_municipality_name(obj):
        """
        Retrieves the municipality's name.
        """
        return obj.municipality.name


class LocalReservationSerializer(serializers.Serializer):
    """
    Serializer for local reservations made at the agency and their signatures.
    """

    signature = serializers.CharField(
        min_length=ETICKET_SIGNATURE_SEGMENT_LENGTH * ETICKET_SIGNATURE_SEGMENTS_COUNT,
        max_length=ETICKET_SIGNATURE_SEGMENT_LENGTH * ETICKET_SIGNATURE_SEGMENTS_COUNT,
    )


class ReservationSerializer(serializers.ModelSerializer):
    """
    serializer for the Reservation model.
    """

    is_still_valid = serializers.SerializerMethodField(read_only=True)
    people_waiting = serializers.SerializerMethodField(read_only=True)
    total_people_waiting = serializers.SerializerMethodField(read_only=True)
    last_booked_ticket = serializers.SerializerMethodField(read_only=True)
    service_name = serializers.CharField(source="service.name", read_only=True)
    agency_name = serializers.CharField(source="service.agency.name", read_only=True)

    class Meta:
        model = Reservation
        fields = "__all__"

    @staticmethod
    def get_last_booked_ticket(reservation: Reservation) -> int:
        """
        Return the last booked ticket number for the reservation's service.
        """
        # The reservation is of type Reservation && Reservation has a service as fk
        return reservation.service.last_booked_ticket

    @staticmethod
    def get_people_waiting(obj: Reservation):
        """
        Return the number of people waiting in ahead if the user
        """
        return obj.get_people_ahead()

    @staticmethod
    def get_total_people_waiting(obj: Reservation):
        """
        Return the total number of people waiting in the service
        """
        return obj.service.get_people_waiting()

    @staticmethod
    def get_is_still_valid(obj):
        """
        Return True if the reservation is still valid.
        """
        if obj.ticket_num != None and obj.ticket_num >= obj.service.current_ticket:
            return True
        return False


class EticketScoringSerializer(serializers.Serializer):
    """E ticket scoring data serializer"""

    latitude = serializers.FloatField(required=True)
    longitude = serializers.FloatField(required=True)
    transporation_method = serializers.CharField(required=False, default="DRIVING")

    def validate_transporation_method(self, data):
        """Check for a known transportation methods"""
        if not data in TransporationMethods._member_names_:
            raise serializers.ValidationError("Transporation method not exist")
        return data
