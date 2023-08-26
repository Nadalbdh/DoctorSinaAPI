import logging

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import mixins, status
from rest_framework.generics import RetrieveAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from backend.decorators import IsValidGenericApi
from backend.forms import MunicipalityActivationForm, MunicipalityOnboardingForm
from backend.models import Municipality
from backend.serializers.serializers import (
    MunicipalityFeatureSerializer,
    MunicipalityMetadataSerializer,
    MunicipalitySerializer,
)
from backend.services.municipality_onboarding import MunicipalityOnBoardingService
from backend.services.notify_new_managers import NotifyNewManagerService
from settings.custom_permissions import (
    IsManagerOrReadOnly,
    MunicipalityManagerPermission,
    OpenEndpointsAny,
)

logger = logging.getLogger("default")

CACHE_FOR = 60 * 15  # 15 minutes


def can_see_ambassadors_forms(
    view_func=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url="admin:login"
):
    """
    Decorator for views that checks that the user is logged in and is a staff
    member, redirecting to the login page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.citizen.see_ambassadors_forms,
        login_url=login_url,
        redirect_field_name=redirect_field_name,
    )
    if view_func:
        return actual_decorator(view_func)
    return actual_decorator


# Municipality Getters
@IsValidGenericApi()
@method_decorator([cache_page(CACHE_FOR)], name="dispatch")
class MunicipalityView(RetrieveUpdateAPIView):
    permission_classes = [IsManagerOrReadOnly]
    queryset = Municipality.objects.all()
    model = Municipality
    serializer_class = MunicipalitySerializer
    lookup_url_kwarg = "municipality_id"

    def get(self, request, municipality_id):
        municipality = get_object_or_404(Municipality, id=municipality_id)
        return Response(data=municipality.to_dict())


@IsValidGenericApi()
@method_decorator([cache_page(CACHE_FOR)], name="dispatch")
class MunicipalityMeta(RetrieveAPIView):
    permission_classes = [OpenEndpointsAny]
    queryset = Municipality.objects.all()
    model = Municipality
    serializer_class = MunicipalityMetadataSerializer
    lookup_url_kwarg = "municipality_route_name"

    def get(self, request, municipality_route_name):
        try:
            municipality = None
            for m in self.get_queryset():
                if m.get_route_name() == municipality_route_name:
                    municipality = m

            if municipality is None:
                raise Municipality.DoesNotExist

            return Response(
                data=municipality.to_simplified_dict(), status=status.HTTP_200_OK
            )
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


@IsValidGenericApi()
@method_decorator([cache_page(CACHE_FOR)], name="dispatch")
class MunicipalitiesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """
        [optional: is_active arg: True/False]
        """
        is_active = request.GET.get("is_active", "empty")
        if is_active.lower() == "true":
            municipalities = Municipality.objects.filter(is_active=True)
        elif is_active.lower() == "false":
            municipalities = Municipality.objects.filter(is_active=False)
        else:
            municipalities = Municipality.objects.all()
        returned_result = [
            municipality.to_simplified_dict() for municipality in municipalities
        ]
        return Response(data=returned_result)


@IsValidGenericApi(post=False)
class MunicipalityFollowView(APIView):
    """
    Add municipality with provided id to the followed municipalities of the
    current user.
    Return codes:
        - 200: Follow executed successfully
        - 404: municipality id is invalid
    """

    def post(self, request, id):
        municipality = get_object_or_404(Municipality, pk=id)
        # TODO Refactor this (decorator)
        if not hasattr(request.user, "citizen"):
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        request.user.citizen.municipalities.add(municipality)
        return Response(
            data={
                "followed_municipalities": list(
                    request.user.citizen.municipalities.values_list("id", flat=True)
                )
            }
        )


@IsValidGenericApi(post=False)
class MunicipalityUnFollowView(APIView):
    """
    Remove municipality with provided id from followed municipalities of the
    current user.
    Return codes:
        - 200: Unfollow executed successfully
        - 404: municipality id is invalid
    """

    def post(self, request, id):
        municipality = get_object_or_404(Municipality, pk=id)
        # TODO Refactor this (decorator)
        if not hasattr(request.user, "citizen"):
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        request.user.citizen.municipalities.remove(municipality)
        return Response(
            data={
                "followed_municipalities": list(
                    request.user.citizen.municipalities.values_list("id", flat=True)
                )
            }
        )


class GenericFormView(APIView):
    # TODO maybe use decorators?
    form_class = None
    template = None

    def on_valid_form_post(self, form):
        raise RuntimeError("on_valid_form_post() must be overwritten")

    def post(self, request):
        form = self.form_class(request.data, request.FILES)
        if form.is_valid():
            try:
                return self.on_valid_form_post(form)
            except Exception as e:
                logger.exception("Onboarding failed %s", e)
                return Response(
                    data={
                        "success": False,
                        "details": f"Error, please contact the developers: {e}",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(
            data={"success": False, "details": form.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def get(self, request):
        form = self.form_class()
        return render(request, self.template, {"form": form})


@method_decorator(can_see_ambassadors_forms, name="dispatch")
class MunicipalityOnboardingView(GenericFormView):
    form_class = MunicipalityOnboardingForm
    template = ("onboarding_template.html",)

    SIGNED_TEXT = """The municipality is <span class="alert-link"> only signed. </span> Please use the other form later for activation."""
    SUCCESS_TEMPLATE = """Onboarding successfull. The password is <span href="#" class="alert-link">{} </span>. Make sure to save it. {}"""

    def on_valid_form_post(self, form):
        municipality_service = MunicipalityOnBoardingService(
            form.cleaned_data["municipality"]
        )
        password = municipality_service.on_board(form.cleaned_data)
        municipality_service.sign()
        extra_text = self.SIGNED_TEXT

        # notification should be the last step
        # todo: make this async task
        NotifyNewManagerService(
            form.cleaned_data["municipality"],
            form.cleaned_data["manager_number"],
            form.cleaned_data["manager_email"],
            password,
        ).notify_first_manager()

        return Response(
            data={
                "success": True,
                "details": self.SUCCESS_TEMPLATE.format(password, extra_text),
            }
        )


@method_decorator(can_see_ambassadors_forms, name="dispatch")
class ActivateMunicipalityView(GenericFormView):
    form_class = MunicipalityActivationForm
    template = ("onboarding_activation_template.html",)

    ERROR_MESSAGE = (
        "No manager exists for the municipality. Please do the onboading first"
    )
    SUCCESS_MESSAGE_DICT = {
        "Activate": "Municipality successfuly signed and activated.",
        "Sign Contract": "Muncipality successfuly signed",
        "Deactivate": "Municipality successfuly deactivated.",
    }

    def on_valid_form_post(self, form):
        operation = form.cleaned_data["operation"]
        if operation == "Activate":
            municipality = form.cleaned_data["inactive_municipality"]
            if municipality.managers.count() == 0:
                return Response(data={"success": False, "details": self.ERROR_MESSAGE})
            municipality_service = MunicipalityOnBoardingService(
                form.cleaned_data["municipality"]
            )
            municipality_service.activate()
            password = municipality_service.on_board(form.cleaned_data)
            NotifyNewManagerService(
                form.cleaned_data["municipality"],
                form.cleaned_data["manager_number"],
                form.cleaned_data["manager_email"],
                password,
            ).send_activation_email_notification()

        if operation == "Sign Contract":
            municipality = form.cleaned_data["inactive_municipality"]
            MunicipalityOnBoardingService(municipality).sign()
        if operation == "Deactivate":
            municipality = form.cleaned_data["active_municipality"]
            MunicipalityOnBoardingService(municipality).deactivate()
        return Response(
            data={"success": True, "details": self.SUCCESS_MESSAGE_DICT[operation]}
        )


@IsValidGenericApi()
class UpdateMunicipalityFeature(mixins.UpdateModelMixin, GenericViewSet):
    serializer_class = MunicipalityFeatureSerializer
    model = Municipality
    permission_classes = (MunicipalityManagerPermission,)
    queryset = Municipality.objects.all()
    lookup_url_kwarg = "municipality_id"
