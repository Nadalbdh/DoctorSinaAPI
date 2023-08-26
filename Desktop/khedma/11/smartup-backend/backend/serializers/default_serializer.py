import base64
import binascii
import imghdr

from django.db.models import FileField, ImageField
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from backend.functions import convert_base64_to_file, convert_base64_to_image


class DefaultSerializer(serializers.Serializer):
    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        model = type(instance)
        for key, value in validated_data.items():
            if isinstance(model._meta.get_field(key), ImageField):
                value = (
                    None
                    if value is None
                    else convert_to_image(value, validated_data.get("title"))
                )
                setattr(instance, key, value)
            elif isinstance(model._meta.get_field(key), FileField):
                value = (
                    None
                    if value is None
                    else convert_to_file(value, validated_data.get("title"))
                )
                setattr(instance, key, value)
            else:
                setattr(instance, key, value)
        instance.save()
        return instance


def convert_to_file(base_64_file, title):
    return convert_base64_to_file(base_64_file, "{}_{}".format(title, timezone.now()))


def convert_to_image(base_64_image, title):
    return convert_base64_to_image(base_64_image, "{}_{}".format(title, timezone.now()))


def validator_string_is_base_64_img(data: str):
    try:
        if len(data.split(";base64,")) != 2:
            raise Exception(" not enough values to unpack ")
        header, encoded_data = data.split(";base64,")
        content_type = header.split(":")[-1]
        if not content_type.startswith("image/"):
            raise ValueError("Unsupported file type")
        decoded_data = base64.b64decode(encoded_data)
        if imghdr.what(None, decoded_data) is None:
            raise ValueError("Invalid image data")
    except (ValueError, TypeError, AttributeError, binascii.Error, Exception) as exc:
        raise ValidationError("Invalid base64 image: " + str(exc))
