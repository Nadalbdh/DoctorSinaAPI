from datetime import datetime

from django.db.models import F
from pytz import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from backend.serializers.fields import ImageField
from polls.models import Choice, Poll


class ChoiceSerializer(serializers.ModelSerializer):
    total_votes = serializers.SerializerMethodField(read_only=True)
    total_local_votes = serializers.SerializerMethodField(read_only=True)
    picture = ImageField(required=False)
    # Used for checks
    municipality = serializers.IntegerField(write_only=True)

    class Meta:
        model = Choice
        exclude = ["voters"]

    @staticmethod
    def get_total_votes(obj):
        """
        All votes for a specific choice
        """
        now_tunis = datetime.now(timezone("Africa/Tunis"))
        if now_tunis > obj.poll.ends_at or obj.poll.live_results:
            return obj.voters.count()
        return "Not available now"

    @staticmethod
    def get_total_local_votes(obj):
        """
        Votes made by citizen having the same registration_municipality
        as the poll municipality for a specific choice
        """
        now_tunis = datetime.now(timezone("Africa/Tunis"))
        if now_tunis > obj.poll.ends_at or obj.poll.live_results:
            return obj.voters.filter(
                citizen__registration_municipality=obj.poll.municipality.pk
            ).count()
        return "Not available now"

    def validate(self, data):
        """
        Check that poll is related to the municipality
        """
        # It's ugly but needed , so that manager cannot create choices for other polls
        municipality = data["municipality"]
        del data["municipality"]
        if municipality != data["poll"].municipality.id:
            raise ValidationError({"message": "You don't have permission on this poll"})
        return data


class PollSerializer(serializers.ModelSerializer):
    picture = ImageField(required=False)
    total_participants = serializers.SerializerMethodField(read_only=True)
    total_votes = serializers.SerializerMethodField(read_only=True)
    total_local_votes = serializers.SerializerMethodField(read_only=True)
    total_local_participants = serializers.SerializerMethodField(read_only=True)
    already_voted = serializers.SerializerMethodField(read_only=True)
    choices = ChoiceSerializer(many=True, read_only=True)
    remaining_time = serializers.ReadOnlyField(read_only=True)
    starts_in = serializers.ReadOnlyField(read_only=True)
    status = serializers.ReadOnlyField(read_only=True)

    class Meta:
        model = Poll
        fields = "__all__"

    @staticmethod
    def get_total_participants(obj):
        """
        All participants for a specific poll
        """
        return (
            obj.choices.filter(voters__isnull=False)
            .values_list("voters", flat=True)
            .distinct()
            .count()
        )

    @staticmethod
    def get_total_votes(obj):
        """
        All votes for a specific poll
        """
        return (
            obj.choices.filter(voters__isnull=False)
            .values_list("voters", flat=True)
            .count()
        )

    def get_total_local_participants(self, obj):
        """
        Votes made by citizen having the same registration_municipality
        as the poll municipality per pool
        """
        return self.filter_local_citizen_votes(obj).distinct().count()

    def get_total_local_votes(self, obj):
        """
        Votes made by citizen having the same registration_municipality
        as the poll municipality all choices
        """
        return self.filter_local_citizen_votes(obj).count()

    def get_already_voted(self, obj):
        request = self.context.get("request")
        return (
            request.user.pk
            in obj.choices.all().values_list("voters", flat=True).distinct()
        )

    @staticmethod
    def filter_local_citizen_votes(obj):
        """
        Helper function to filter votes of citizen with their registered municipality
        """
        return (
            obj.choices.filter(voters__isnull=False)
            .annotate(registered_mun=F("voters__citizen__registration_municipality"))
            .values("voters", "registered_mun")
            .filter(registered_mun=obj.municipality.pk)
        )
