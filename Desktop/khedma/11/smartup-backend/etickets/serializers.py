import json

from rest_framework import serializers

from etickets.helper_functions import ETicketsHelper
from etickets.models import Agency, Reservation


class ReservationSerializer(serializers.ModelSerializer):
    ticket_info_json = serializers.SerializerMethodField(read_only=True)
    ticket_info = serializers.CharField(write_only=True)

    class Meta:
        model = Reservation
        fields = "__all__"
        read_only_fields = ["created_at"]

    @staticmethod
    def get_ticket_info_json(obj):
        return json.loads(obj.ticket_info)


class AgencySerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Agency
        exclude = [
            "base_url",
            "authentication_user",
            "authentication_password",
            "num_agency",
        ]
        read_only_fields = [f.name for f in Agency._meta.get_fields()]

    @staticmethod
    def get_status(obj):
        if ETicketsHelper.check_valid_time(agency=obj, serializer=True):
            return "Open"
        return "Closed"
