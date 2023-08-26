import logging
from distutils.util import strtobool

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import Subquery
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import mixins, status, viewsets
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rules.contrib.rest_framework import AutoPermissionViewSetMixin
from url_filter.integrations.drf import DjangoFilterBackend

from backend.decorators import IsValidGenericApi
from backend.enum import StatusLabel
from backend.functions import get_image_url, is_citizen, is_municipality_manager
from backend.mixins import (
    BaseViewMixin,
    CountableObjectMixin,
    CreateDossierRelatedModelMixin,
    CRUDCollectionMixin,
    CRUDObjectMixin,
    ElBaladiyaModelViewSet,
    ElBaladiyaNestedModelViewSet,
    ElBaladiyaPermissionViewSetMixin,
    GetCollectionMixin,
    GetObjectMixin,
    PrivacyMixin,
    PrivateOnlyMixin,
    SetCreatedByMixin,
    UpdateStatusMixin,
)
from backend.models import (
    Appointment,
    Attachment,
    Building,
    Comment,
    Complaint,
    ComplaintCategory,
    Dossier,
    DossierAttachment,
    Event,
    Municipality,
    News,
    Procedure,
    Reaction,
    Region,
    Report,
    Reservation,
    SubjectAccessRequest,
    Topic,
)
from backend.notification_helpers import excerpt_notification
from backend.serializers.serializers import (
    AppointmentSerializer,
    AttachmentSerializer,
    BuildingSerializer,
    CommentCreateSerializer,
    CommentUpdateSerializer,
    ComplaintSerializer,
    CustomUpdateStatusSerializer,
    DefaultSerializer,
    DossierAttachmentSerializer,
    DossierSerializer,
    EventCreateSerializer,
    EventDisinterestSerializer,
    EventInterestSerializer,
    EventParticipateSerializer,
    EventUnparticipateSerializer,
    EventUpdateSerializer,
    NewsCreateSerializer,
    NewsUpdateSerializer,
    ProcedureCreateSerializer,
    ProcedureUpdateSerializer,
    ReactionSerializer,
    RegionCreateSerializer,
    RegionUpdateSerializer,
    ReportCreateSerializer,
    ReportUpdateSerializer,
    ReservationSerializer,
    SubjectAccessRequestSerializer,
    TopicSerializer,
)
from emails.templatetags.status_translation import status_translate
from notifications.enums import NotificationActionTypes
from settings.custom_permissions import MunicipalityManagerWriteOnlyPermission

logger = logging.getLogger("default")


# SAR CRUD
@method_decorator([cache_page(10)], name="dispatch")
class SubjectAccessRequestViewSet(
    PrivateOnlyMixin,
    SetCreatedByMixin,
    PrivacyMixin,
    CountableObjectMixin,
    UpdateStatusMixin,
    ElBaladiyaModelViewSet,
):
    model = SubjectAccessRequest
    serializer_class = SubjectAccessRequestSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = [
        "created_at",
    ]


# Category CRUD - Deprecated 04.06.2021
@IsValidGenericApi()
@method_decorator([cache_page(60)], name="dispatch")
class ComplaintCategoryView_Deprecated(GetObjectMixin, GenericAPIView):
    serializer_class = DefaultSerializer
    model = ComplaintCategory

    def get_queryset(self, **kwargs):
        return self.model.objects.all()

    def get_object(self, **kwargs):
        kwargs.pop("municipality_id")
        return super().get_object(**kwargs)


@IsValidGenericApi()
@method_decorator([cache_page(60)], name="dispatch")
class ComplaintCategoriesView_Deprecated(GetCollectionMixin, GenericAPIView):
    serializer_class = DefaultSerializer
    model = ComplaintCategory

    def get_queryset(self, **kwargs):
        return self.model.objects.all()


@IsValidGenericApi()
@method_decorator([cache_page(60)], name="dispatch")
class ComplaintCategoryView(GetObjectMixin, GenericAPIView):
    serializer_class = DefaultSerializer
    model = ComplaintCategory


@IsValidGenericApi()
@method_decorator([cache_page(60)], name="dispatch")
class ComplaintCategoriesView(GetCollectionMixin, GenericAPIView):
    serializer_class = DefaultSerializer
    model = ComplaintCategory


# Region CRUD
@IsValidGenericApi()
@method_decorator([cache_page(60)], name="dispatch")
class RegionView(CRUDObjectMixin, GenericAPIView):
    serializer_class = RegionUpdateSerializer
    model = Region


@IsValidGenericApi()
@method_decorator([cache_page(60)], name="dispatch")
class RegionsView(CRUDCollectionMixin, GenericAPIView):
    serializer_class = RegionCreateSerializer
    model = Region


@method_decorator([cache_page(10)], name="dispatch")
class ComplaintViewSet(
    PrivateOnlyMixin,
    SetCreatedByMixin,
    PrivacyMixin,
    CountableObjectMixin,
    UpdateStatusMixin,
    ElBaladiyaPermissionViewSetMixin,
    ElBaladiyaModelViewSet,
):
    """
    The Complaint CRUD
    """

    serializer_class = ComplaintSerializer
    model = Complaint

    def get_queryset(self):
        queryset = super().get_queryset()
        municipality_id = self.kwargs["municipality"]
        manager_filter = self.request.GET.get("manager_category_filter", "") == "True"
        if manager_filter and is_municipality_manager(
            self.request.user, municipality_id
        ):
            categories = self.request.user.manager.complaint_categories.all()
            return queryset.filter(category__in=Subquery(categories.values("pk")))
        return queryset

    notification_title = "تحيين في مشكل خاص بي"


# Dossier CRUD
@IsValidGenericApi()
@method_decorator([cache_page(10)], name="dispatch")
class DossierViewSet(
    SetCreatedByMixin,
    UpdateStatusMixin,
    ElBaladiyaPermissionViewSetMixin,
    ElBaladiyaModelViewSet,
):
    serializer_class = DossierSerializer
    model = Dossier


# Building CRUD
@IsValidGenericApi()
class BuildingViewSet(
    CreateDossierRelatedModelMixin,
    AutoPermissionViewSetMixin,
    ElBaladiyaNestedModelViewSet,
):
    serializer_class = BuildingSerializer
    model = Building
    related_model = Dossier


# Dossier attachment CRUD
@IsValidGenericApi()
class DossierAttachmentViewSet(
    CreateDossierRelatedModelMixin,
    AutoPermissionViewSetMixin,
    ElBaladiyaNestedModelViewSet,
):
    serializer_class = DossierAttachmentSerializer
    model = DossierAttachment


# Comments CRUD
@IsValidGenericApi()
@method_decorator([cache_page(10)], name="dispatch")
class CommentView(CountableObjectMixin, CRUDObjectMixin, GenericAPIView):
    serializer_class = CommentUpdateSerializer
    model = Comment


@IsValidGenericApi()
@method_decorator([cache_page(10)], name="dispatch")
class CommentsView(CRUDCollectionMixin, GenericAPIView):
    serializer_class = CommentCreateSerializer
    model = Comment
    title = "اضافة تعليق لمنشورك"
    template = ' تم اضافة تعليق جديد  "{}" لمنشورك " {}".'

    def notify(self, response, municipality_id):
        parent = Municipality.objects.get(pk=municipality_id).all_comments.get(
            pk=response["parent_comment_id"]
        )
        user = parent.created_by
        body = self.template.format(response["excerpt"], parent.title)
        user.notifications.create(
            title=self.title,
            body=body,
            subject_type=ContentType.objects.get_for_model(self.model),
            subject_object=parent,
            action_type=NotificationActionTypes.OPEN_SUBJECT,
            municipality=parent.municipality,
        )

    def post(self, request, serializer, **kwargs):
        # FIXME
        serializer.validated_data["created_by"] = request.user
        response = super().post(request, serializer, **kwargs)
        if response.status_code != status.HTTP_201_CREATED:
            return response
        response_json = response.data
        return Response(response_json, status.HTTP_201_CREATED)

    def get(self, request, **kwargs):
        """
        Returns all objects
        """

        objects = (
            Comment.posts.all()
            if strtobool(request.GET.get("parent_comments", "True"))
            else Comment.comments.all()
        )
        objects = objects.filter(municipality_id=kwargs["municipality_id"]).order_by(
            "-created_at"
        )

        if "page" in request.GET or "per_page" in request.GET:
            objects = self.do_paging(objects, request)

        collection = [self.to_dict(obj, user=request.user) for obj in objects]
        return Response(data=collection)


@IsValidGenericApi()
class CommentUpdateStatusView(UpdateStatusMixin, BaseViewMixin, GenericAPIView):
    """Comment status update API endpoint"""

    serializer_class = CustomUpdateStatusSerializer
    model = Comment


# Topics CRUD
@IsValidGenericApi()  # Could be eventually removed, the only use-case now is to log the warnings
class TopicViewSet(ElBaladiyaModelViewSet):
    serializer_class = TopicSerializer
    model = Topic
    permission_classes = [MunicipalityManagerWriteOnlyPermission]


# News CRUD
@IsValidGenericApi()
@method_decorator([cache_page(10)], name="dispatch")
class NewsObjectView(CountableObjectMixin, CRUDObjectMixin, GenericAPIView):
    serializer_class = NewsUpdateSerializer
    model = News
    permission_classes = [MunicipalityManagerWriteOnlyPermission]


@IsValidGenericApi()
@method_decorator([cache_page(10)], name="dispatch")
class NewsView(CRUDCollectionMixin, GenericAPIView):
    serializer_class = NewsCreateSerializer
    model = News
    permission_classes = [MunicipalityManagerWriteOnlyPermission]


# Procedure CRUD
@IsValidGenericApi()
@method_decorator([cache_page(10)], name="dispatch")
class ProcedureView(CRUDObjectMixin, GenericAPIView):
    """Procedure API endpoint"""

    serializer_class = ProcedureUpdateSerializer
    model = Procedure
    permission_classes = [MunicipalityManagerWriteOnlyPermission]


@IsValidGenericApi()
@method_decorator([cache_page(10)], name="dispatch")
class ProceduresView(CRUDCollectionMixin, GenericAPIView):
    """
    Procedures endpoint
    """

    serializer_class = ProcedureCreateSerializer
    model = Procedure
    permission_classes = [MunicipalityManagerWriteOnlyPermission]


# Report CRUD
@IsValidGenericApi()
class ReportView(CountableObjectMixin, CRUDObjectMixin, GenericAPIView):
    serializer_class = ReportUpdateSerializer
    model = Report
    permission_classes = [MunicipalityManagerWriteOnlyPermission]


@IsValidGenericApi()
class ReportsView(CRUDCollectionMixin, GenericAPIView):
    serializer_class = ReportCreateSerializer
    model = Report
    permission_classes = [MunicipalityManagerWriteOnlyPermission]


# Event CRUD
@IsValidGenericApi()
@method_decorator([cache_page(10)], name="dispatch")
class EventView(CRUDObjectMixin, GenericAPIView):
    serializer_class = EventUpdateSerializer
    model = Event
    permission_classes = [MunicipalityManagerWriteOnlyPermission]


@IsValidGenericApi()
@method_decorator([cache_page(10)], name="dispatch")
class EventsView(CRUDCollectionMixin, GenericAPIView):
    serializer_class = EventCreateSerializer
    model = Event
    permission_classes = [MunicipalityManagerWriteOnlyPermission]


@IsValidGenericApi()
class EventParticipateView(BaseViewMixin, GenericAPIView):
    serializer_class = EventParticipateSerializer
    model = Event

    def post(self, request, serializer, **kwargs):
        event = self.get_object(**kwargs)
        citizen = request.user.citizen
        participate = serializer.validated_data.get("participate", True)
        if participate:
            event.participants.add(citizen)
        else:
            event.participants.remove(citizen)
        return Response(status=status.HTTP_200_OK)


# DEPRECATED, use EventParticipateView instead
@IsValidGenericApi()
class EventUnparticipateView(BaseViewMixin, GenericAPIView):
    serializer_class = EventUnparticipateSerializer
    model = Event

    def post(self, request, serializer, **kwargs):
        event = self.get_object(**kwargs)
        citizen = request.user.citizen
        event.participants.remove(citizen)
        return Response(status=status.HTTP_200_OK)


@IsValidGenericApi()
class EventInterestView(BaseViewMixin, GenericAPIView):
    serializer_class = EventInterestSerializer
    model = Event

    def post(self, request, serializer, **kwargs):
        event = self.get_object(**kwargs)
        citizen = request.user.citizen
        interest = serializer.validated_data.get("interest", True)
        if interest:
            event.interested_citizen.add(citizen)
        else:
            event.interested_citizen.remove(citizen)
        return Response(status=status.HTTP_200_OK)


# DEPRECATED, use EventInterestView instead
@IsValidGenericApi()
class EventDisinterestView(BaseViewMixin, GenericAPIView):
    serializer_class = EventDisinterestSerializer
    model = Event

    def post(self, request, serializer, **kwargs):
        event = self.get_object(**kwargs)
        citizen = request.user.citizen
        event.interested_citizen.remove(citizen)
        return Response(status=status.HTTP_200_OK)


@IsValidGenericApi()
class ReactionsView(GenericAPIView):
    serializer_class = ReactionSerializer
    model = Reaction

    def post(self, request, serializer, **kwargs):
        """
        Creates and returns object
        return codes:
            - 201: element created successfully
        """
        serializer.validated_data["user_id"] = request.user.id
        serializer.create(serializer.validated_data)
        return HttpResponse(status=status.HTTP_201_CREATED)


class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    queryset = Appointment.objects.all()
    http_method_names = ["get", "post"]

    def get_queryset(self):
        """
        limit manager visibility to only appointments which they review
        """
        user = self.request.user
        queryset = Appointment.objects.all()
        if is_municipality_manager(user):
            queryset = queryset.filter(reviewed_by=user.manager)
        return queryset

    def create(self, request, *args, **kwargs):
        user = self.request.user
        if is_municipality_manager(user):
            # Autofill field if they're not passed to the request
            request.data["suggested_by"] = request.data.get(
                "suggested_by", user.manager.id
            )
            request.data["reviewed_by"] = request.data.get(
                "reviewed_by", [user.manager.id]
            )
        return super().create(request, *args, **kwargs)


class ReservationViewSet(viewsets.ModelViewSet):
    """
    Handle reservations
    """

    serializer_class = ReservationSerializer
    http_method_names = ["get", "post", "patch"]

    def get_queryset(self):
        """
        For citizens, limit their visibility to only their reservations
        """
        user = self.request.user
        queryset = Reservation.objects.all()
        if is_citizen(user):
            queryset = queryset.filter(citizen=user.citizen)
        return queryset

    def create(self, request):
        """
        Autofill the citizen value, if a citizen is logged in
        """
        if is_citizen(request.user):
            request.data["citizen"] = request.user.citizen.id
        return super().create(request)


@IsValidGenericApi()
class ReservationStatusView(UpdateStatusMixin, BaseViewMixin, GenericAPIView):
    """
    Reservation status update API endpoint
    This focuses only on the manager's side of the reservation
    TODO: Limit access to only manager with permission
    """

    serializer_class = CustomUpdateStatusSerializer
    model = Reservation

    def to_dict(self, obj, **kwargs):
        return ReservationSerializer(obj).data


class AttachmentViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    Handle attachement upload to reservations,
    A citizen should only be able to associate attachement to his own reservations.
    Please note that adding attachement to a reservation should be after the creation of reservation
    """

    serializer_class = AttachmentSerializer
    queryset = Attachment.objects.all()

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reservation = serializer.validated_data["reservation"]
        user = request.user
        if is_citizen(request.user) and user.citizen != reservation.citizen:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class FeedView(GetCollectionMixin, APIView):
    @staticmethod
    def scramble_feed(data, page_size):
        """
        This method is used to convert data from 3 lists (events, news and reports) into ONE list of objects
        """
        events, news, reports = data.values()
        result = []
        for i in range(int(page_size)):
            if i < len(events):
                result.append({"type": "event", "object": events[i]})
            if i < len(news):
                result.append({"type": "news_object", "object": news[i]})
            if i < len(reports):
                result.append({"type": "report", "object": reports[i]})
        return result

    def get(self, request, *args, **kwargs):
        municipality_id = kwargs["municipality_id"]
        events = Event.objects.filter(municipality_id=municipality_id)
        news = News.objects.filter(municipality_id=municipality_id)
        reports = Report.objects.filter(municipality_id=municipality_id)

        if "page" in request.GET or "per_page" in request.GET:
            events = self.do_paging(events, request)
            news = self.do_paging(news, request)
            reports = self.do_paging(reports, request)

        data = {
            "events": [event.to_dict(request.user) for event in events],
            "news": [news_object.to_dict(request.user) for news_object in news],
            "reports": [report.to_dict() for report in reports],
        }

        result = self.scramble_feed(
            data, request.GET.get("per_page", max(len(events), len(reports), len(news)))
        )
        return JsonResponse(data=result, safe=False)


@method_decorator([cache_page(20)], name="dispatch")
class GetProfilePictureView(APIView):
    def get(self, request, *args, **kwargs):
        user = get_object_or_404(User, pk=kwargs["id"])
        return Response(
            {"profile_picture": get_image_url(user.citizen.profile_picture)}
        )


class GetStatusLabeling(APIView):
    permission_classes = [
        AllowAny,
    ]

    def get(self, request, *args, **kwargs):
        return Response(StatusLabel.get_choices(), status=status.HTTP_200_OK)
