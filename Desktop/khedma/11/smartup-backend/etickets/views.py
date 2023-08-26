import json
import logging
from datetime import datetime

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import HttpResponse
from rest_framework import mixins, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_simplejwt.backends import TokenBackend
from rest_framework_simplejwt.exceptions import TokenBackendError

from backend.decorators import IsValidGenericApi
from backend.mixins import ElBaladiyaGenericViewSet
from etickets.helper_functions import ETicketsHelper
from etickets.models import Agency, Reservation
from etickets.serializers import AgencySerializer, ReservationSerializer

SERVICE_MAPPING = {
    "BIRTH CERTIFICATE": 1,
    "LEGALIZED SIGNATURE": 2,
    "LEGALIZED COPY": 3,
}
logger = logging.getLogger("default")


@IsValidGenericApi()
class ReservationViewSet(mixins.CreateModelMixin, ElBaladiyaGenericViewSet):
    """
    This class is used to make a reservation for e-tickets (via POST), also to fetch citizen reservation
    """

    serializer_class = ReservationSerializer
    model = Reservation

    def create(self, request, *args, **kwargs):
        # FIXME there must be a better way to do this
        request.data["created_by"] = request.user.pk
        request.data["service_name"] = "default"
        request.data["ticket_info"] = "default"
        request.data["ticket_num"] = 1
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        api_resp = ETicketsHelper.handle_api_reservation_response(
            user=request.user,
            agency_id=kwargs["agency"],
            service_id=request.data.get("service_id"),
        )
        request.data["service_name"] = (
            api_resp.get("infoticket").get("ticket").get("service")
        )
        request.data["ticket_num"] = (
            api_resp.get("infoticket").get("ticket").get("numeroticket")
        )
        request.data["ticket_info"] = json.dumps(
            api_resp.get("infoticket").get("ticket")
        )
        resp = super().create(request, *args, **kwargs)
        logger.info(
            "Reservation to %s created by  %s",
            request.data["service_name"],
            request.user,
        )
        return resp

    def get_queryset(self):
        base_queryset = super().get_queryset()

        return base_queryset.filter(created_by=self.request.user)


@IsValidGenericApi()
class AgencyViewSet(ReadOnlyModelViewSet, ElBaladiyaGenericViewSet):
    """
    This class is used to fetch agencies and their corresponding available services
    """

    serializer_class = AgencySerializer
    model = Agency
    permission_classes = [AllowAny]

    def retrieve(self, request, *args, **kwargs):
        """
        Return agency details
        """
        resp = super().retrieve(request, *args, **kwargs)
        agency_data = ETicketsHelper.get_agency_detail(agency_id=resp.data.get("id"))
        resp.data.update(agency_data)
        return resp


@IsValidGenericApi()
class GetCurrentReservation(APIView):
    def get(self, request, agency_id):
        """
        Returns all reserved & valid tickets for the logged user
        """
        data = ETicketsHelper.get_reserved_tickets(
            agency_id=agency_id, user_id=request.user.id
        )
        return Response(data, status=200)


class MyETicketPDF(APIView):
    template_name = "eticket.html"
    permission_classes = [
        AllowAny,
    ]

    @staticmethod
    def get_filename():
        time = datetime.today()
        today = time.strftime("%d_%m_%Y")
        return f"eticket_{today}.pdf"

    def get(self, request, agency_id, service):
        """
        Return a PDF for the logged user containing his eticket for a service based on agency
        """
        user = None
        if bool(request.user and request.user.is_authenticated):
            user = request.user
        else:
            bearer = request.GET.get("bearer")
            try:
                data = TokenBackend(algorithm="HS256").decode(bearer, verify=False)
                user = User.objects.get(pk=data["user_id"])
            except TokenBackendError:
                return Response(
                    {"message": "Not Authorized"}, status=HTTP_401_UNAUTHORIZED
                )

        data = ETicketsHelper.get_reserved_tickets(
            agency_id=agency_id, user_id=user.pk
        ).get("tickets")
        if not data:
            raise ValidationError({"error": "You have no reservation"})

        ticket = next(
            (ticket for ticket in data if ticket["id_service"] == service), None
        )
        if ticket:
            filename = MyETicketPDF.get_filename()
            pdf = ETicketsHelper.generate_pdf(ticket, agency_id)
            response = HttpResponse(pdf, content_type="application/pdf")
            response["Content-Disposition"] = 'attachment; filename="' + filename + '"'
            return response
        raise ValidationError({"error": "You have no reservation for this service"})


class TicketNotificationView(APIView):
    permission_classes = [AllowAny]
    model = Agency

    def handle_reservation_notification(
        self, current_ticket, current_active_ticket, active_reservations
    ):
        if current_active_ticket:
            msg = (
                f"الرجاء التوجه للشباك ببلدية {current_active_ticket.agency.municipality.name} للتمتع بخدمة "
                f"{current_active_ticket.service_name}",
            )
            current_active_ticket.created_by.notifications.create(
                title=msg,
                body=msg,
                subject_type=ContentType.objects.get_for_model(self.model),
            )

        # Notify citizen with current_ticket_num+1 ... current_ticket_num+5 if exists
        for reservation in active_reservations.exclude(ticket_num=current_ticket):
            diff_num = reservation.ticket_num - current_ticket
            msg = ""
            if diff_num == 1:
                msg = (
                    f"أمامك شخص واحد في صف خدمة {reservation.service_name} ببلدية "
                    f"{reservation.agency.municipality.name}"
                )
            elif diff_num == 2:
                msg = (
                    f"أمامك شخصان في صف خدمة {reservation.service_name} ببلدية "
                    f"{reservation.agency.municipality.name}"
                )
            else:
                msg = (
                    f"أمامك {diff_num} أشخاص  في صف خدمة {reservation.service_name} ببلدية "
                    f"{reservation.agency.municipality.name}"
                )
            notification = reservation.created_by.notifications.create(
                title=msg,
                body=msg,
                subject_type=ContentType.objects.get_for_model(self.model),
            )

    def post(self, request):
        """
        Notify citizen having the current processed ticket and the next 5 ticket holder ( if exists in reservations)
        """
        # We need to add some sort of authentication on this endpoint
        x_forward_for = request.META.get("HTTP_X_FORWARDED_FOR", None)
        try:
            server_ip = x_forward_for.split(",")[0]
        except AttributeError:
            return Response({"message": "Not a valid ip"}, status=HTTP_400_BAD_REQUEST)
        #
        # FOR TEST PURPOSE
        # payload = request.data
        # server_ip = '41.231.54.66'
        if server_ip:
            try:
                agency = self.model.objects.get(base_url__icontains=server_ip)
            except self.model.DoesNotExist:
                return Response(
                    {"real_ip": server_ip, "x-forward-for": x_forward_for},
                    status=HTTP_404_NOT_FOUND,
                )

        else:
            raise ValidationError({"message": "Not a valid server ip"})
        payload = json.loads(request.data)
        current_ticket = int(payload.get("num_ticket"))
        service_id = int(payload.get("service_id"))
        today = datetime.today().date()
        # Get active reservations with ticket_num in range [current_ticket +1 ...current_ticket + 5]
        # by service_id & agency_id
        active_reservations = Reservation.objects.filter(
            Q(created_at__date=today)
            & Q(agency=agency)
            & Q(service_id=service_id)
            & Q(ticket_num__range=[current_ticket, current_ticket + 5])
        )
        if not active_reservations:
            return Response(
                {"message": "All reservations are made locally"},
                status=status.HTTP_202_ACCEPTED,
            )
        # Check if a citizen has current_ticket to notify him with custom message
        current_active_ticket = active_reservations.filter(
            ticket_num=current_ticket
        ).first()
        # FIXME Make this an async job
        self.handle_reservation_notification(
            current_ticket, current_active_ticket, active_reservations
        )

        return Response(
            {"message": "Notifications sent successfully"}, status=status.HTTP_200_OK
        )
