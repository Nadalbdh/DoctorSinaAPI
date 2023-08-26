import base64
import binascii
import string
import subprocess
import uuid
from random import choice

from django.core.files.base import ContentFile
from rest_framework.exceptions import ValidationError

chars = string.ascii_letters + string.digits  # Python 3
random_string = lambda x: "".join(choice(chars) for _ in range(x))


# Standard Files
def convert_base64_to_file(base64_str: str, file_name: str) -> ContentFile:
    # Remove any newline characters and replace any URL-safe characters that may have been replaced with underscores
    base64_data = base64_str.replace("\n", "").replace("_", "/").replace("-", "+")

    # Decode the URL-safe base64-encoded data to binary and create the ContentFile object
    binary_data = base64.urlsafe_b64decode(base64_data)
    return ContentFile(binary_data, name=file_name + ".pdf")


def get_file_url(file):
    return file.url if file else None


# Images
def convert_base64_to_image(base64_string, file_name):
    try:
        if len(base64_string.split(";base64,")) != 2:
            raise Exception("not enough values to unpack")
        header, encoded_data = base64_string.split(";base64,")
        content_type = header.split(":")[-1]
        extension = content_type.split("/")[-1]
        if extension == "svg+xml":
            extension = "svg"
        file_name = f"{uuid.uuid4().hex}.{extension}"
        image_data = base64.b64decode(encoded_data)
        return ContentFile(image_data, name=file_name)
    except (ValueError, TypeError, AttributeError, binascii.Error, Exception) as exc:
        raise ValidationError("Invalid base64 image: " + str(exc))


def convert_image_to_base64(image):
    if image is None:
        return None
    return "data:image/{};base64,{}".format(
        image.name.split(".")[-1], base64.b64encode(image.read()).decode("utf-8")
    )


def get_image_url(image):
    return image.url if image else None
    """  This needs to be refactored in a helper in the project scope because it is used in multiple apps"""


def get_manager_username_from_phone_number(phone_number):
    return "M{}".format(phone_number)


def get_manager_phone_number_from_username(username):
    return username.partition("M")[2]


def is_citizen(user):
    """
    Checks if user is a citizen
    """
    return hasattr(user, "citizen")


def is_manager(user):
    """
    Checks if user is a manager
    """
    return hasattr(user, "manager")


def is_municipality_manager(user, municipality_id=None):
    """
    Checks if the passed user is a manager,
    if municipality_id is passed, it also checks if that manager
    belongs the municipality with that id
    """
    if not municipality_id:
        return hasattr(user, "manager")
    return hasattr(user, "manager") and user.manager.municipality.id == municipality_id


def get_citizen_from_request(request):
    """
    Returns a citizen object from a request
    Note: If the user is not logged in as a citizen, it will return None
    """
    return request.user.citizen if is_citizen(request.user) else None


def server_works(adrss: str, timeout=2) -> bool:
    """ping a server address to check if it works"""
    try:
        response = subprocess.run(
            f"curl --connect-timeout {timeout} --max-time {timeout} --fail {adrss}",
            shell=True,
            check=True,
            timeout=timeout,
        )
        return response.returncode == 0
    except Exception as e:
        return False
