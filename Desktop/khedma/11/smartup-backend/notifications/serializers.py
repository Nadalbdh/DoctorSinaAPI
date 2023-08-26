from rest_framework import serializers

from backend.serializers.default_serializer import DefaultSerializer
from backend.serializers.serializers import MunicipalityMetadataSerializer

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    municipality = MunicipalityMetadataSerializer()
    model = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Notification
        fields = "__all__"

    def get_model(self, obj):
        return obj.subject_type.name if obj.subject_type else None


class FollowDossierSerializer(DefaultSerializer):
    # unique_identifier is a different field
    # don't confuse it with "id/pk"
    unique_identifier = serializers.CharField(max_length=20)
    cin_digits = serializers.CharField(max_length=3, min_length=3)


class FollowComplaintSerializer(DefaultSerializer):
    id = serializers.IntegerField(min_value=1)


class FollowSubjectAccessRequestSerializer(DefaultSerializer):
    id = serializers.IntegerField(min_value=1)


class FollowCommentSerializer(DefaultSerializer):
    id = serializers.IntegerField(min_value=1)
