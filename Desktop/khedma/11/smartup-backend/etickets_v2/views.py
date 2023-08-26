import logging
from datetime import date, timedelta
from uuid import UUID

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.views import APIView
from rest_framework_api_key.permissions import HasAPIKey

from backend.decorators import IsValidGenericApi
from backend.enum import TransporationMethods
from backend.exceptions import NotHandledLocally
from backend.mixins import (
    ElBaladiyaGenericViewSet,
    ElBaladiyaModelViewSet,
    SetCreatedByMixin,
)
from backend.models import Municipality
from etickets_v2.helpers import (
    closest_agency,
    decrypt_signature,
    generate_pdf,
    get_filename,
    get_service_prefix,
)
from etickets_v2.models import Agency, Reservation, Service
from etickets_v2.serializers import (
    AgencySerializer,
    EticketScoringSerializer,
    LocalReservationSerializer,
    ReservationSerializer,
    ServiceSerializer,
)
from notifications.enums import NotificationActionTypes
from notifications.models import Notification
from settings.custom_permissions import (
    DefaultPermission,
    MunicipalityManagerWriteOnlyPermission,
)

logger = logging.getLogger("default")


@IsValidGenericApi()
class ServicesView(ElBaladiyaModelViewSet):
    serializer_class = ServiceSerializer
    model = Service
    permission_classes = [HasAPIKey | MunicipalityManagerWriteOnlyPermission]
    basename = "service"

    def create(self, request, *args, **kwargs):
        """
        HTTP_400_BAD_REQUEST: A service with this name already exists
        """
        if type(request.data) != dict:
            request.data._mutable = True
        agency = get_object_or_404(Agency, id=kwargs["agency"])
        if agency.is_existing_name(request.data["name"]):
            raise ValidationError("A service with this name already exists.")

        prefix = get_service_prefix(agency)
        request.data["name"] = f"{prefix}-{request.data['name']}"
        request.data["created_by_id"] = request.user.pk
        request.data["created_by"] = request.user.pk
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        """
        Get a list of services provided by an agency.
        """
        if "municipality" in self.kwargs:
            self.kwargs.pop("municipality")
        return self.model.objects.filter(**self.kwargs)

    def list(self, request, municipality, agency, *args, **kwargs):
        """
        get a list of services provided by agency

          [optional: is_active arg: "True" | "False" ]
        """
        is_active = request.GET.get("is_active") == "True"
        if is_active:
            services = Service.objects.filter(
                agency__municipality=municipality,
                agency=UUID(agency),
                is_active=is_active,
            )
        else:
            services = Service.objects.filter(
                agency__municipality=municipality, agency=UUID(agency)
            )
        return Response(data=[ServiceSerializer(service).data for service in services])

    @action(
        detail=True,
        methods=["post"],
        url_path="send_notifications",
        url_name="send_notifications",
        permission_classes=[HasAPIKey],
    )
    def send_notifications(self, request, pk, *args, **kwargs):
        """Send push notifications for the last five active reservations for a given service.
        HTTP_201_CREATED: Notifications were sent successfully!
        """
        reservations = Reservation.valid_objects.filter(
            service__pk=pk,
            is_active=True,
        ).order_by("-id")[
            :5:-1  # notify last 5 people
        ]
        notifications = []
        for reservation in reservations:
            body, title = reservation.notification_content()
            notifications.append(
                Notification(
                    user=reservation.created_by,
                    title=title,
                    body=body,
                    subject_type=ContentType.objects.get_for_model(Reservation),
                    subject_object=reservation,
                    action_type=NotificationActionTypes.ETICKET_RESERVATION,
                    municipality=reservation.service.agency.municipality,
                )
            )
        Notification.objects.bulk_create(notifications)
        return Response(
            data={"message": "notifications were sent successfully!"},
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=False,
        methods=["patch"],
        url_path="push_all",
        url_name="push_all",
        permission_classes=[HasAPIKey],
    )
    def push_all(self, request, *args, **kwargs):
        """used by local backend to push (sync) a list of services
        HTTP_201_CREATED: services synced successfully!
        """
        services = request.data
        for service in services:
            service_id = service["id"]
            exists = Service.objects.filter(pk=service_id).exists()
            if exists:
                instance = Service.objects.get(id=service_id)
                serializer = self.get_serializer(instance, data=service, partial=True)
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
                instance.reset_counter_to_zero()

        return Response(
            data={"message": "services synced successfully!"},
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["get"],
        url_path="book",
        url_name="book",
        permission_classes=[DefaultPermission],
    )
    def book(self, request, agency, pk, *args, **kwargs):
        """
        HTTP_201_CREATED: success
        HTTP_400_BAD_REQUEST: user already has an e-ticket for this service
        HTTP_404_NOT_FOUND: service not found
        HTTP_429_TOO_MANY_REQUESTS: user have reached the booking limit for today
        HTTP_500_INTERNAL_SERVER_ERROR: could not reach local server
        """
        has_booked = Reservation.valid_objects.filter(
            created_by=request.user,
            is_active=True,
            service__pk=pk,
        ).exists()

        if has_booked:
            return Response(
                data={"message": "user already has an e-ticket for this service."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        today_eticket_reservations = Reservation.objects.filter(
            created_at__date=date.today(),
            created_by=request.user,
        ).count()
        if today_eticket_reservations >= settings.MAX_NB_TICKETS_PER_DAY_FOR_USER:
            return Response(
                data={"message": "user have reached the booking limit for today"},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        agency = (
            Agency.objects.filter(pk=UUID(agency))
            .values("local_ip", "secured_connection")
            .first()
        )
        service = get_object_or_404(Service, id=pk)
        booking = service.create_booking_locally()
        if booking.status_code != status.HTTP_201_CREATED:
            return Response(
                data={"message": f"could't create eticket."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        service.last_booked_ticket = booking.json()["last_booked_ticket"]
        service.save()
        reservation = Reservation.objects.create(
            ticket_num=service.last_booked_ticket,
            created_by=request.user,
            service=service,
        )
        return Response(data=ReservationSerializer(reservation).data)


@IsValidGenericApi()
class AgenciesView(SetCreatedByMixin, ElBaladiyaModelViewSet):
    serializer_class = AgencySerializer
    model = Agency
    permission_classes = [
        MunicipalityManagerWriteOnlyPermission,
    ]
    basename = "agencie"

    def list(self, request, municipality, *args, **kwargs):
        """
        Returns a list of all agencies for a particular municipality.
        [optional: is_active arg: "True"]
        """
        is_active = request.GET.get("is_active") == "True"
        if is_active:
            agencies = Agency.objects.filter(is_active=True, municipality=municipality)
        else:
            agencies = Agency.objects.filter(municipality=municipality)
        result = AgencySerializer(agencies, many=True).data
        return Response(data=result)

    @action(
        detail=False,
        methods=["get"],
        url_path="reservations",
        url_name="all_agencies_reservations",
        permission_classes=[DefaultPermission],
    )
    def all_agencies_reservations(self, request, municipality, *args, **kwargs):
        """
        Returns a list of all reservations in all agencies of a particular municipality for a particular user.
        HTTP_200_OK: Success.
        """
        data = ReservationSerializer(
            Reservation.valid_objects.filter(
                created_by=request.user,
                is_active=True,
                service__agency__municipality=municipality,
            ),
            many=True,
        ).data
        return Response(data=data, status=status.HTTP_200_OK)


@IsValidGenericApi()
class ReservationsView(ElBaladiyaGenericViewSet):
    """
    A viewset for managing reservations.
    """

    serializer_class = ReservationSerializer
    model = Reservation
    permission_classes = [
        DefaultPermission,
    ]
    basename = "reservations"

    def get_queryset(self):
        if "municipality" in self.kwargs:
            self.kwargs.pop("municipality")
        return self.model.objects.filter(**self.kwargs)

    def list(self, request, agency, *args, **kwargs):
        """return all reservation in an agency for a particular user
        HTTP_200_OK: success
        """
        data = ReservationSerializer(
            Reservation.valid_objects.filter(
                service__agency=agency,
                created_by=request.user,
                is_active=True,
            ),
            many=True,
        ).data
        return Response(data=data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["get"],
        url_path="pdf",
        url_name="pdf_reservation",
        permission_classes=[DefaultPermission],
    )
    def pdf_reservation(self, request, agency, pk, *args, **kwargs):
        """
        Returns a PDF file of the reservation for download.
        HTTP_200_OK: success
        HTTP_404_NOT_FOUND: could not find reservation
        HTTP_400_BAD_REQUEST: could not generate pdf
        """
        try:
            reservation = get_object_or_404(
                Reservation,
                pk=pk,
                created_by=request.user,
                service__agency=agency,
                ticket_num__gte=F("service__current_ticket"),
                is_active=True,
                created_at__date=date.today(),
            )
            pdf = generate_pdf(ReservationSerializer(reservation).data)
            response = HttpResponse(pdf, content_type="application/pdf")
            response["Content-Disposition"] = (
                'attachment; filename="' + get_filename() + '"'
            )
            return response
        except Exception as e:
            return Response(
                data={"message": f"could't generate a PDF: {e}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=False,
        methods=["get"],
        url_path=r"(?P<slug>[^/.]+)/verify",
        url_name="verify_reservation",
        permission_classes=[DefaultPermission],
    )
    def verify_reservation(self, request, municipality, agency, slug, *args, **kwargs):
        """
        Verify if a reservation can be made for a service.
        Returns:
        bool: True if reservation can be made, False otherwise.
        """
        yesterday = date.today() - timedelta(days=1)
        is_valid = Reservation.objects.filter(
            service__agency=agency,
            pk=slug,
            created_at__gt=yesterday,
        ).exists()
        return Response(data=is_valid, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["post"],
        url_path=r"cancel",
        url_name="cancel_reservation",
        permission_classes=[DefaultPermission],
    )
    def cancel_reservation(self, request, municipality, agency, pk, *args, **kwargs):
        """
        HTTP_200_OK: success
        HTTP_202_ACCEPTED: successfully executed on remote, but couldn't record operation on the local server
        HTTP_404_NOT_FOUND: could not find reservation
        Returns:
            Reservation: the reservation canceled
        """
        reservation = get_object_or_404(
            self.model,
            created_by=request.user,
            id=pk,
            service__agency=agency,
            service__agency__municipality=municipality,
        )

        if reservation.ticket_num <= reservation.service.current_ticket:
            return Response(
                {"message": "Reservation no longer cancelable"},
                status=status.HTTP_404_NOT_FOUND,
            )
        reservation.is_active = False
        reservation.save()
        data = ReservationSerializer(reservation).data
        try:
            response = reservation.cancel_locally()
            if response.status_code != status.HTTP_200_OK:
                raise NotHandledLocally
        except NotHandledLocally as e:
            return Response(data=data, status=e.ERROR_STATUS)
        return Response(data=data, status=status.HTTP_200_OK)


@IsValidGenericApi()
class LocalReservationsView(CreateAPIView):
    """A view for making a reservation at a local agency."""

    serializer_class = LocalReservationSerializer
    model = Reservation
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        The signature is a string of length 6
        Examples:
            - re11xa
            - kad32w
            - a12fhb
            - 25ca21

            HTTP_201_CREATED: Success.
            HTTP_404_NOT_FOUND: signature no longer valid
            HTTP_403_FORBIDDEN: this reservation already exits
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        [service_id, ticket_num] = decrypt_signature(
            serializer.validated_data["signature"]
        )

        reservation_exists = self.model.objects.filter(
            ticket_num=ticket_num,
            service__pk=service_id,
            service__agency__municipality=kwargs["municipality"],
        ).exists()
        service_exists = Service.objects.filter(
            id=service_id,
            last_booked_ticket__gte=ticket_num,
            current_ticket__lt=ticket_num,
        ).exists()

        if reservation_exists:
            return Response(status=status.HTTP_403_FORBIDDEN)

        if not service_exists:
            return Response(status=status.HTTP_404_NOT_FOUND)

        service = get_object_or_404(
            Service,
            pk=service_id,
            last_booked_ticket__gte=ticket_num,
            current_ticket__lt=ticket_num,
        )
        reservation = Reservation.objects.create(
            ticket_num=ticket_num,
            created_by=request.user,
            service=service,
            is_physical=True,
        )
        reservation.save()
        return Response(
            data=ReservationSerializer(reservation).data, status=status.HTTP_201_CREATED
        )


@IsValidGenericApi()
class EticketScoringView(APIView):
    """
    A view to score an e-ticket based on the user's location and
    the transportation method.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = EticketScoringSerializer

    def post(self, request, serializer: Serializer, *args, **kwargs):
        """
        HTTP_200_OK: success
        HTTP_400_BAD_REQUEST: invalid data provided
        HTTP_404_NOT_FOUND: Agency Not Found.
        """
        municipality = get_object_or_404(Municipality, id=kwargs["municipality"])
        transporation_method = serializer.validated_data.get("transporation_method")
        agency = closest_agency(
            serializer.validated_data.get("latitude"),
            serializer.validated_data.get("longitude"),
            Agency.objects.filter(municipality=municipality),
            TransporationMethods[transporation_method],
        )
        if agency is None:
            return Response(
                {"message": "Agency Not Found"}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(AgencySerializer(agency).data, status=status.HTTP_200_OK)


class GetAllAgenciesView(ListAPIView):
    """
    A view to get a list of all agencies.
    """

    queryset = Agency.objects.all()
    serializer_class = AgencySerializer

    def get(self, request):
        """
        HTTP_200_OK: success
        """
        # Note the use of `get_queryset()` instead of `self.queryset`
        queryset = self.get_queryset()
        serializer = AgencySerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
