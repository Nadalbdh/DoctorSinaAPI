from rest_framework import serializers

from emails.models import Email


class MailingListSerializer(serializers.Serializer):
    emails = serializers.ListField(child=serializers.EmailField())


class EMailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Email
        fields = ["email"]
