import logging

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers, status
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from backend.enum import OsTypes
from backend.exceptions import DeprecatedUsername
from backend.functions import get_manager_username_from_phone_number
from backend.models import RegisteredDevice

logger = logging.getLogger("default")


def _check_deprecated_username(data):
    if "username" in data:
        raise DeprecatedUsername


class CitizenLoginSerializer(TokenObtainPairSerializer):
    device_unique_id = serializers.CharField(max_length=50, required=False)
    phone_number = serializers.CharField(min_length=8, max_length=8)
    os = serializers.ChoiceField(required=False, choices=OsTypes.get_choices())
    os_version = serializers.CharField(required=False)
    fcm_token = serializers.CharField(required=False)
    last_version = serializers.CharField(required=False)
    model = serializers.CharField(required=False)
    product = serializers.CharField(required=False)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data, user):
        fields = [
            "os",
            "os_version",
            "fcm_token",
            "last_login",
            "last_version",
            "product",
        ]
        temp = {
            field: validated_data[field] for field in fields if field in validated_data
        }
        temp["user"] = user
        instance, _ = RegisteredDevice.objects.update_or_create(
            device_unique_id=validated_data["device_unique_id"],
            defaults=temp,
        )
        return instance

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["user_id"] = user.id
        token["phone_number"] = user.username
        token["first_name"] = user.first_name
        token["last_name"] = user.last_name
        return token


class CitizenLoginView(TokenObtainPairView):
    serializer_class = CitizenLoginSerializer

    def post(self, request, *args, **kwargs):
        """
        Note: Attribute: 'username' is no longer used, Please use 'phone_number' instead
        :return:
                - 200 if login succeeded
                - 401 if login failed
        """
        _check_deprecated_username(request.data)
        request.data["username"] = request.data["phone_number"]
        response = super(CitizenLoginView, self).post(request, *args, **kwargs)
        if response.status_code != status.HTTP_200_OK:
            return response
        # Get user
        user = User.objects.get(username=request.data["username"])
        response.data["first_login"] = user.citizen.first_login
        response.data[
            "preferred_municipality_id"
        ] = user.citizen.preferred_municipality_id
        response.data[
            "latest_residence_update_date"
        ] = user.citizen.latest_residence_update_date
        response.data["is_active"] = user.is_active
        user.citizen.set_first_login()
        # Get device
        if "device_unique_id" in request.data:
            serializer = CitizenLoginSerializer(data=request.data)
            serializer.create(request.data, user)
        return response


class ManagerLoginSerializer(TokenObtainPairSerializer):
    device_unique_id = serializers.CharField(max_length=50, required=False)
    phone_number = serializers.CharField(min_length=8, max_length=8)
    os = serializers.ChoiceField(required=False, choices=OsTypes.get_choices())
    os_version = serializers.CharField(required=False)
    fcm_token = serializers.CharField(required=False)
    last_version = serializers.CharField(required=False)
    model = serializers.CharField(required=False)
    product = serializers.CharField(required=False)

    def create(self, validated_data, user):
        fields = [
            "os",
            "os_version",
            "fcm_token",
            "last_login",
            "last_version",
            "product",
        ]
        temp = {
            field: validated_data[field] for field in fields if field in validated_data
        }
        temp["user"] = user
        instance, _ = RegisteredDevice.objects.update_or_create(
            device_unique_id=validated_data["device_unique_id"],
            defaults=temp,
        )
        return instance

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["user_id"] = user.id
        token["phone_number"] = user.username
        token["first_name"] = user.first_name
        token["last_name"] = user.last_name
        return token


class ManagerLoginView(TokenObtainPairView):
    serializer_class = ManagerLoginSerializer

    def post(self, request, *args, **kwargs):
        """
        :return:
                - 200 if login succeeded
                - 401 if login failed/ user doesn't have permissions for specified municipality
        """
        _check_deprecated_username(request.data)
        request.data["username"] = get_manager_username_from_phone_number(
            request.data["phone_number"]
        )
        response = super(ManagerLoginView, self).post(request, *args, **kwargs)
        if response.status_code != status.HTTP_200_OK:
            return response

        user = authenticate(
            username=request.data["username"], password=request.data["password"]
        )
        if not hasattr(user, "manager"):
            raise InvalidToken()

        municipality = user.manager.municipality
        response.data["municipality_id"] = municipality.id
        if "device_unique_id" in request.data:
            serializer = ManagerLoginSerializer(data=request.data)
            serializer.create(request.data, user)
        return response
