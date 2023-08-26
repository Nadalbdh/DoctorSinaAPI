import re

from rest_framework.exceptions import ValidationError


def validate_digits(value, exception=ValidationError):
    is_valid = re.match(r"^[234759]\d{7}$", value)
    if not is_valid:
        raise exception("Phone number is not valid")
