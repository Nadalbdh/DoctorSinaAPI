from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from guardian.shortcuts import get_perms, get_users_with_perms
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from backend.decorators import IsValidGenericApi
from backend.enum import MunicipalityPermissions
from backend.functions import get_manager_username_from_phone_number
from backend.helpers import generate_default_password
from backend.mixins import CRUDCollectionMixin, CRUDObjectMixin
from backend.models import Committee, ComplaintCategory, Municipality
from backend.reset_password import (
    check_reset_password_otp,
    generate_jwt_token,
    prepare_reset_password_otp,
)
from backend.serializers.serializers import ResetPasswordSerializer, VerifyOTPSerializer
from backend.serializers.serializers_managers import (
    CommitteeCreateSerializer,
    CommitteeUpdateSerializer,
    ManagerChangePasswordSerializer,
    ManagerCreateSerializer,
    ManagerUpdateSerializer,
)
from backend.services.notify_new_managers import NotifyNewManagerService
from settings.custom_permissions import (
    IsManagerOrReadOnly,
    MunicipalityManagerWriteOnlyPermission,
)


@IsValidGenericApi()
class ManagerView(GenericAPIView):
    serializer_class = ManagerUpdateSerializer

    def put(self, request, serializer, **kwargs):
        """
        return codes:
            - 201: User permissions updated successfully
            - 401: permission denied
        """
        user = get_object_or_404(User, id=serializer.validated_data["user_id"])
        has_general_permission = request.user.has_perm(
            MunicipalityPermissions.MANAGE_PERMISSIONS,
            Municipality.objects.get(pk=kwargs["municipality_id"]),
        )
        if not (has_general_permission or user == request.user):
            return Response(
                data={
                    "message": "You don't have enough permissions to access this part"
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
        serializer.update(user, serializer.validated_data)
        # Temporary ( Adding sub-category to user )
        cc = ComplaintCategory.objects.all()
        if (
            user.has_perm(
                MunicipalityPermissions.MANAGE_COMPLAINTS,
                Municipality.objects.get(pk=kwargs["municipality_id"]),
            )
            and not user.manager.complaint_categories.all()
        ):
            user.manager.complaint_categories.add(*cc)
        if not user.has_perm(
            MunicipalityPermissions.MANAGE_COMPLAINTS,
            Municipality.objects.get(pk=kwargs["municipality_id"]),
        ):
            user.manager.complaint_categories.remove(*cc)
        return Response(status=status.HTTP_200_OK)

    def get(self, request, user_id, **kwargs):
        """
        Returns manager by id
        return codes:
            - 200: permissions fetched successfully
            - 404: element not found
        """
        user = get_object_or_404(User, id=user_id)
        municipality = get_object_or_404(Municipality, pk=kwargs["municipality_id"])
        permissions = get_perms(user, municipality)
        return Response(data={**(user.manager.to_dict()), "permissions": permissions})

    def delete(self, request, user_id, **kwargs):
        """
        Inactivates manager by id
        return codes:
            - 200: user disabled successfully
            - 404: element not found
        """
        user = get_object_or_404(User, id=user_id)
        user.is_active = False
        user.save()
        return Response(status=status.HTTP_200_OK)


@IsValidGenericApi()
class ManagersView(GenericAPIView):
    serializer_class = ManagerCreateSerializer
    permission_classes = [IsManagerOrReadOnly | HasAPIKey]

    def post(self, request, serializer, **kwargs):
        """
        creates a user and manager inside the db
        return codes:
            - 201: New User added successfully
            - 401: permission denied
            - 409: username not available
        """
        if not request.user.has_perm(
            MunicipalityPermissions.MANAGE_PERMISSIONS,
            Municipality.objects.get(pk=kwargs["municipality_id"]),
        ):
            return Response(
                data={
                    "message": "You don't have enough permissions to access this part"
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if User.objects.filter(
            username=get_manager_username_from_phone_number(
                serializer.validated_data["phone_number"]
            )
        ).exists():
            return Response(
                data={"message": "User with this username already exists"},
                status=status.HTTP_409_CONFLICT,
            )
        user = serializer.create(serializer.validated_data)
        password = generate_default_password(user)
        # Temporary ( Adding sub-category to user )
        cc = ComplaintCategory.objects.all()
        if user.has_perm(
            MunicipalityPermissions.MANAGE_COMPLAINTS,
            Municipality.objects.get(pk=kwargs["municipality_id"]),
        ):
            user.manager.complaint_categories.add(*cc)
        NotifyNewManagerService(
            user.manager.municipality,
            serializer.validated_data["phone_number"],
            serializer.validated_data["email"],
            password,
        ).notify_another_manager()
        return Response(data=user.manager.to_dict(), status=status.HTTP_201_CREATED)

    def get(self, request, **kwargs):
        """
        Returns all managers with a list of permissions for each one
        """
        manager_users = get_users_with_perms(
            get_object_or_404(Municipality, pk=kwargs.get("municipality_id")),
            attach_perms=True,
        )
        formatted_result = [
            {**user.manager.to_dict(), "permissions": manager_users[user]}
            for user in manager_users
        ]
        return Response(data=formatted_result)


@IsValidGenericApi()
class ManagerChangePasswordView(GenericAPIView):
    serializer_class = ManagerChangePasswordSerializer

    def post(self, request, serializer, **kwargs):
        """
        change password of one of the managers of a municipality
        return codes:
            - 202: Password changed successfully
            - 401: wrong old password
            - 404: wrong user_id
            - 406: new password not acceptable
        """
        user = get_object_or_404(User, id=kwargs["user_id"])
        if not (
            user == request.user
            or request.user.has_perm(
                MunicipalityPermissions.MANAGE_PERMISSIONS,
                Municipality.objects.get(pk=kwargs["municipality_id"]),
            )
        ):
            return Response(
                data={
                    "message": "You don't have enough permissions to access this part"
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if "old_password" in serializer.validated_data and not user.check_password(
            serializer.validated_data["old_password"]
        ):
            return Response(
                data={"message": "wrong old password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            user.set_password(serializer.validated_data["new_password"])
            user.save()
        except:
            return Response(
                data={"message": "new pin not accepted"},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        return Response(status=status.HTTP_202_ACCEPTED)


@IsValidGenericApi()
class ManagerResetPassword(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = ResetPasswordSerializer

    def post(self, request, serializer, **kwargs):
        """
        Reset manager password using sms or email
        :param request:
        :param serializer:
        :param kwargs:
        :return:
        """
        phone_number = serializer.validated_data["phone_number"]
        user = get_object_or_404(User, username=f"M{phone_number}")
        prepare_reset_password_otp(
            user, phone_number=phone_number, type=serializer.validated_data["type"]
        )
        return HttpResponse(status=status.HTTP_201_CREATED)


@IsValidGenericApi()
class ManagerResetPasswordVerifyOTP(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = VerifyOTPSerializer

    def post(self, request, serializer, **kwargs):
        """
        verify reset password OTP
        :param request:
        :param serializer:
        :param kwargs:
        :return:
        """
        phone_number = serializer.validated_data["phone_number"]
        otp = serializer.validated_data["otp"]
        otp_check_result = check_reset_password_otp(phone_number, otp)
        if not otp_check_result:
            return JsonResponse(
                data={"message": "Wrong OTP"}, status=status.HTTP_401_UNAUTHORIZED
            )
        user = User.objects.get(username=f"M{phone_number}")
        user.is_active = True
        user.save()
        tokens = generate_jwt_token(user)
        return JsonResponse(
            data={
                **tokens,
                "connected_user_id": user.id,
                "municipality_id": user.manager.municipality.pk,
            },
            status=status.HTTP_202_ACCEPTED,
        )


# Committee CRUD
@IsValidGenericApi()
class CommitteeView(CRUDObjectMixin, GenericAPIView):
    serializer_class = CommitteeUpdateSerializer
    model = Committee
    permission_classes = [MunicipalityManagerWriteOnlyPermission]


@IsValidGenericApi()
class CommitteesView(CRUDCollectionMixin, GenericAPIView):
    serializer_class = CommitteeCreateSerializer
    model = Committee
