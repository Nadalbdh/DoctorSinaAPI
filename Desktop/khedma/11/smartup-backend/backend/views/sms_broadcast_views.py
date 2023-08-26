from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateView
from rest_framework import status, viewsets
from rest_framework.parsers import JSONParser
from rest_framework.response import Response

from backend.enum import SMSBroadcastRequestStatus
from backend.functions import is_municipality_manager
from backend.models import Municipality, SMSBroadcastRequest
from backend.serializers.serializers import SMSBroadcastRequestSerializer


def can_see_broadcast_forms(
    view_func=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url="admin:login"
):
    """
    Decorator for views that checks that the user is logged in and is a staff
    member, redirecting to the login page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.citizen.see_broadcast_forms,
        login_url=login_url,
        redirect_field_name=redirect_field_name,
    )
    if view_func:
        return actual_decorator(view_func)
    return actual_decorator @ method_decorator(staff_member_required, name="dispatch")


@method_decorator(can_see_broadcast_forms, name="dispatch")
class SMSBroadcastRequestReviewView(TemplateView):
    template_name = "sms_broadcast_request_review.html"


@method_decorator(can_see_broadcast_forms, name="dispatch")
class SMSBroadcastView(TemplateView):
    template_name = "sms_broadcast.html"

    def get_context_data(self, **kwargs):
        context = super(SMSBroadcastView, self).get_context_data(**kwargs)
        context["municipalities"] = Municipality.objects.all()
        return context


class SMSBroadcastRequestViewSet(viewsets.ModelViewSet):
    serializer_class = SMSBroadcastRequestSerializer
    queryset = SMSBroadcastRequest.objects.all()
    parser_classes = (JSONParser,)

    def create(self, request, *args, **kwargs):
        if not request.user.is_staff and not is_municipality_manager(request.user):
            return Response(
                data={"message": "Not allowed"}, status=status.HTTP_401_UNAUTHORIZED
            )
        if is_municipality_manager(request.user):
            request.data["municipality"] = request.user.manager.municipality.id
            request.data["created_by"] = request.user.manager.id
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        # Pre-approve requests submitted by the staff
        instance = serializer.save()
        if instance.is_created_by_staff():
            instance.set_status_approved()
        return instance

    def retrieve(self, request, *args, **kwargs):
        """
        Return data for single sms request
        """
        if not request.user.is_staff and not is_municipality_manager(request.user):
            return Response(
                data={"message": "Not allowed"}, status=status.HTTP_401_UNAUTHORIZED
            )
        sms_request = self.get_object()
        if is_municipality_manager(request.user):
            if not is_municipality_manager(request.user, sms_request.municipality.id):
                return Response(
                    data={"message": "Not allowed"}, status=status.HTTP_401_UNAUTHORIZED
                )
        serializer = self.serializer_class(sms_request)
        return Response(serializer.data)

    def list(self, request):
        """
        List SMS Broadcast requests,
        if a manager is logged in, it only shows the requests which belongs to his municipality
        """
        if not request.user.is_staff and not is_municipality_manager(request.user):
            return Response(
                data={"message": "Not allowed"}, status=status.HTTP_401_UNAUTHORIZED
            )

        sms_requests = self.get_queryset()

        if is_municipality_manager(request.user):
            # Shows only SMS Broadcast requests associated to the manager's municipality
            sms_requests = sms_requests.filter(
                municipality=request.user.manager.municipality.id
            )
        else:
            # Propritize PENDING SMS Broadcast requests
            order = [choice[0] for choice in SMSBroadcastRequestStatus.get_choices()]
            sms_requests = sorted(sms_requests, key=lambda x: order.index(x.status))

        serializer = self.serializer_class(sms_requests, many=True)
        return Response(serializer.data)

    def partial_update(self, request, pk):
        """
        Updates fields, for now it updates only the status
        """
        if not request.user.is_staff and False:
            return Response(
                data={"message": "Not allowed"}, status=status.HTTP_401_UNAUTHORIZED
            )
        serializer = self.serializer_class(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        sms_broadcast_request = self.get_object()
        sms_broadcast_request.scheduled_on = serializer.validated_data.get(
            "scheduled_on"
        )
        sms_broadcast_request.set_status(serializer.validated_data.get("status"))
        return Response(serializer.to_representation(sms_broadcast_request))
