from rest_framework import serializers


class SignMetabaseEmbedSerializer(serializers.Serializer):
    municipality_name = serializers.CharField(required=False, allow_blank=True)
    municipality_id = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if "municipality_name" in data and "municipality_id" in data:
            raise serializers.ValidationError("only one filter can be applied")

        if "municipality_name" not in data and "municipality_id" not in data:
            raise serializers.ValidationError("at least one filter sould be applied")
        return data
