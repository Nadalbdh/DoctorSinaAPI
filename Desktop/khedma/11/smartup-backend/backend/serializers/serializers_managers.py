from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from guardian.shortcuts import assign_perm, remove_perm
from rest_framework import serializers

from backend.enum import MunicipalityPermissions
from backend.functions import get_manager_username_from_phone_number
from backend.helpers import ManagerHelpers
from backend.models import Committee, ComplaintCategory, Manager, Municipality
from emails.helpers.mailing_list import update_mailing_list

from .default_serializer import DefaultSerializer
from .serializers import PhoneNumberField


def update_permissions(user, municipality, validated_data):
    for permission, _ in MunicipalityPermissions.get_choices():
        attribute_name = permission.lower()

        if attribute_name not in validated_data:
            continue
        elif validated_data[attribute_name]:
            assign_perm(permission, user, municipality)
        else:
            remove_perm(permission, user, municipality)


class ManagerCreateSerializer(DefaultSerializer):
    phone_number = PhoneNumberField()
    name = serializers.CharField(max_length=150, required=False)
    title = serializers.CharField(allow_null=True, required=False)
    email = serializers.EmailField(required=False)
    municipality_id = serializers.IntegerField(min_value=1)

    manage_dossiers = serializers.BooleanField(required=False)
    manage_procedures = serializers.BooleanField(required=False)
    manage_complaints = serializers.BooleanField(required=False)
    manage_reports = serializers.BooleanField(required=False)
    manage_subject_access_requests = serializers.BooleanField(required=False)
    manage_committees = serializers.BooleanField(required=False)
    manage_news = serializers.BooleanField(required=False)
    manage_events = serializers.BooleanField(required=False)
    manage_permissions = serializers.BooleanField(required=False)
    manage_appointments = serializers.BooleanField(required=False)
    manage_polls = serializers.BooleanField(required=False)
    manage_forum = serializers.BooleanField(required=False)
    manage_eticket = serializers.BooleanField(required=False)

    def create(self, validated_data):
        user = User.objects.create(
            username=get_manager_username_from_phone_number(
                validated_data["phone_number"]
            ),
            last_name=validated_data.get("name", ""),
            email=validated_data.get("email", ""),
        )
        municipality = Municipality.objects.get(pk=validated_data["municipality_id"])
        update_permissions(
            user=user, municipality=municipality, validated_data=validated_data
        )
        Manager.objects.create(
            user=user, title=validated_data.get("title", ""), municipality=municipality
        )
        update_mailing_list(municipality, [user.email], append=True)
        return user


class ManagerUpdateSerializer(DefaultSerializer):
    municipality_id = serializers.IntegerField()
    name = serializers.CharField(max_length=150, required=False)
    email = serializers.EmailField(required=False)
    title = serializers.CharField(required=False)
    user_id = serializers.IntegerField(min_value=1)

    manage_dossiers = serializers.BooleanField(required=False)
    manage_procedures = serializers.BooleanField(required=False)
    manage_complaints = serializers.BooleanField(required=False)
    manage_reports = serializers.BooleanField(required=False)
    manage_subject_access_requests = serializers.BooleanField(required=False)
    manage_committees = serializers.BooleanField(required=False)
    manage_news = serializers.BooleanField(required=False)
    manage_events = serializers.BooleanField(required=False)
    manage_permissions = serializers.BooleanField(required=False)
    manage_appointments = serializers.BooleanField(required=False)
    manage_polls = serializers.BooleanField(required=False)
    manage_forum = serializers.BooleanField(required=False)
    manage_eticket = serializers.BooleanField(required=False)

    complaint_categories = serializers.SlugRelatedField(
        slug_field="name",
        queryset=ComplaintCategory.objects.all(),
        required=False,
        many=True,
    )

    def update(self, user, validated_data):
        municipality = Municipality.objects.get(pk=validated_data["municipality_id"])
        update_permissions(
            user=user, municipality=municipality, validated_data=validated_data
        )
        user.manager.title = validated_data.get("title", user.manager.title)
        if "complaint_categories" in validated_data:
            user.manager.complaint_categories.set(
                validated_data["complaint_categories"]
            )
        user.manager.save()
        user.last_name = validated_data.get("name", user.last_name)
        user.email = validated_data.get("email", user.email)
        update_mailing_list(municipality, [user.email], append=True)
        user.save()


class ManagerChangePasswordSerializer(DefaultSerializer):
    old_password = serializers.CharField(required=False)  # optional old_password check
    new_password = serializers.CharField(min_length=1)


class CommitteeCreateSerializer(DefaultSerializer):
    municipality_id = serializers.IntegerField()
    title = serializers.CharField(max_length=255)
    body = serializers.CharField()

    def create(self, validated_data):
        return Committee.objects.create(**validated_data)


class CommitteeUpdateSerializer(DefaultSerializer):
    id = serializers.IntegerField()
    title = serializers.CharField(max_length=255, required=False)
    body = serializers.CharField(required=False)
