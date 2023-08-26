from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny

from backend.decorators import IsValidGenericApi
from backend.registration_otp_manager import (
    check_registration_otp,
    prepare_registration_otp,
)
from backend.reset_password import (
    check_reset_password_otp,
    generate_jwt_token,
    prepare_reset_password_otp,
)
from backend.serializers.serializers import (
    ChangePasswordSerializer,
    EditProfileSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    VerifyOTPSerializer,
)
from sms.enum import SMSQueueStatus


@IsValidGenericApi()
class RegisterView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request, serializer, **kwargs):
        """
        Creates and returns a new user
        => To resend an other random code, you can call this endpoint with the phone number only (all other fields
        being empty)
        return codes:
            - 200: Municipality is not using elBaladiya.tn, user added to wait-list
            - 201: user created successfully
            - 409: user already has active account
        """
        municipality, user = serializer.create(serializer.validated_data)
        if user.is_active:
            return JsonResponse(
                data={"message": "User with this phone number already exists"},
                status=status.HTTP_409_CONFLICT,
            )
        registration_result = prepare_registration_otp(user)
        if registration_result == SMSQueueStatus.TOO_MANY_ATTEMPTS:
            return JsonResponse(
                data={"message": "Too many attempts, try again later"},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        if registration_result == SMSQueueStatus.SENT:
            return HttpResponse(status=status.HTTP_201_CREATED)
        return HttpResponse(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@IsValidGenericApi()
class RegisterVerifyOTPView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = VerifyOTPSerializer

    def post(self, request, serializer, **kwargs):
        """
        Check the veracity of OTP
        return codes:
            - 202: user account activated
            - 409: wrong otp
        """
        phone_number = serializer.validated_data["phone_number"]
        otp = serializer.validated_data["otp"]
        otp_check_result = check_registration_otp(phone_number, otp)
        if not otp_check_result:
            return JsonResponse(
                data={"message": "Wrong OTP"}, status=status.HTTP_401_UNAUTHORIZED
            )
        user = User.objects.get(username=phone_number)
        user.is_active = True
        user.save()
        tokens = generate_jwt_token(user)
        return JsonResponse(data=tokens, status=status.HTTP_202_ACCEPTED)


@IsValidGenericApi()
class RegisterVerifyOTPV2View(GenericAPIView):
    """
    Dear reader,
    Please Do NOT refactor this to remove duplicate code, this is gonna be used over a short period of time to decide
    which view will be kept.
    Thanks,
    Nadhem
    """

    permission_classes = [AllowAny]
    serializer_class = VerifyOTPSerializer

    def post(self, request, serializer, **kwargs):
        """
        Check the veracity of OTP
        return codes:
            - 202: user account activated
            - 409: wrong otp
        """
        phone_number = serializer.validated_data["phone_number"]
        otp = serializer.validated_data["otp"]
        otp_check_result = check_registration_otp(phone_number, otp)
        if not otp_check_result:
            return JsonResponse(
                data={"message": "Wrong OTP"}, status=status.HTTP_401_UNAUTHORIZED
            )
        user = User.objects.get(username=phone_number)
        user.is_active = True
        user.save()
        tokens = generate_jwt_token(user)
        return JsonResponse(data=tokens, status=status.HTTP_202_ACCEPTED)


@IsValidGenericApi()
class ProfileView(GenericAPIView):
    serializer_class = EditProfileSerializer

    def put(self, request, serializer, **kwargs):
        """
        Update user general info once the OTP is verified,
        this step could be skipped /optional
        return codes:
            - 202: citizen updated successfully
        """
        citizen = serializer.update(request.user.citizen, serializer.validated_data)
        return JsonResponse(data=citizen.to_dict(), status=status.HTTP_202_ACCEPTED)

    def get(self, request):
        """
        Returns personal info of current user
        """
        return JsonResponse(data=request.user.citizen.to_dict())


@IsValidGenericApi()
class ResetPassword(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = ResetPasswordSerializer

    def post(self, request, serializer, **kwargs):
        """
        Reset user password using sms or email
        :param request:
        :param serializer:
        :param kwargs:
        :return:
        """
        phone_number = serializer.validated_data["phone_number"]
        user = get_object_or_404(User, username=phone_number)
        prepare_reset_password_otp(
            user, phone_number, type=serializer.validated_data["type"]
        )
        return HttpResponse(status=status.HTTP_201_CREATED)


@IsValidGenericApi()
class ResetPasswordVerifyOTP(GenericAPIView):
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
        user = User.objects.get(username=serializer.validated_data["phone_number"])
        user.is_active = True
        user.save()
        tokens = generate_jwt_token(user)
        return JsonResponse(data=tokens, status=status.HTTP_202_ACCEPTED)


@IsValidGenericApi()
class ChangePassword(GenericAPIView):
    serializer_class = ChangePasswordSerializer

    def post(self, request, serializer, **kwargs):
        """
        Change password after user has confirmed verification code
        :param request:
        :param serializer:
        :param kwargs:
        :return:
        """
        if (
            "old_password" in serializer.validated_data
            and not request.user.check_password(
                serializer.validated_data["old_password"]
            )
        ):
            return JsonResponse(
                data={"message": "wrong old password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        new_password = serializer.validated_data["new_password"]
        request.user.set_password(new_password)
        request.user.save()
        update_session_auth_hash(request, request.user)
        tokens = generate_jwt_token(request.user)
        return JsonResponse(data=tokens, status=status.HTTP_200_OK)
