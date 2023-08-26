import logging

from django.utils import timezone
from rest_framework import serializers

from backend.functions import (
    convert_base64_to_file,
    convert_base64_to_image,
    get_file_url,
    get_image_url,
    random_string,
)
from backend.serializers.default_serializer import validator_string_is_base_64_img

logger = logging.getLogger("default")


class ImageField(serializers.Field):
    def to_representation(self, value):
        return get_image_url(value)

    def to_internal_value(self, data):
        validator_string_is_base_64_img(data)
        return convert_base64_to_image(data, random_string(10))


class Base64FileField(serializers.Field):
    def to_representation(self, value):
        return get_file_url(value)

    def get_title(self):
        try:
            data = self.root.initial_data
            return data["title"]
        except Exception as e:  # pylint: disable=broad-except
            logger.info("Title extraction failed: %s", e)
            return random_string(20)

    def to_internal_value(self, data):
        return convert_base64_to_file(
            data, "{}_{}".format(self.get_title(), timezone.now())
        )
