from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.decorators import IsValidGenericApi
from backend.models import Comment, Complaint, Dossier, SubjectAccessRequest
from backend.serializers.serializers import SubjectAccessRequestSerializer
from settings.custom_permissions import DefaultPermission

from .models import Notification
from .serializers import (
    FollowCommentSerializer,
    FollowComplaintSerializer,
    FollowDossierSerializer,
    FollowSubjectAccessRequestSerializer,
    NotificationSerializer,
)


# Notifications Endpoint
@IsValidGenericApi()
class NotificationsView(APIView):
    model = Notification

    def get(self, request):
        """
        Returns all notifications for the logged in user. Setting recent to True returns the first 50 Notifications
        return codes:
            - 200: notifications returned successfully
        """
        notifications = request.user.notifications.all()
        if request.data.get("recent", False):
            notifications = notifications[:50]
        notifications_dict = [
            NotificationSerializer(notification).data for notification in notifications
        ]
        return Response(
            data={"notifications": notifications_dict}, status=status.HTTP_200_OK
        )


@IsValidGenericApi(post=False)
class AllNotificationsReadView(APIView):
    model = Notification
    permission_classes = [DefaultPermission]

    def post(self, request):
        """
        Marks all notifications for the logged-in user.
        """
        for notification in request.user.notifications.filter(is_read=False):
            notification.mark_as_read()
        return Response(status=status.HTTP_200_OK)


@IsValidGenericApi()
class NotificationView(APIView):
    model = Notification
    serializer = NotificationSerializer

    def get(self, request, id):
        queryset = Notification.objects.get(pk=id)
        return Response(data=self.serializer(queryset).data, status=status.HTTP_200_OK)


@IsValidGenericApi(post=False)
class MarkNotificationRead(APIView):
    model = Notification

    def post(self, request, **kwargs):
        """
        Mark Notification as read
        """
        notification = request.user.notifications.get(pk=kwargs["id"])
        notification.mark_as_read()
        return Response(status=status.HTTP_200_OK)


@IsValidGenericApi()
class FollowDossierView(GenericAPIView):
    serializer_class = FollowDossierSerializer
    model = Dossier
    permission_classes = [DefaultPermission]

    def post(self, request, serializer, **kwargs):
        """
        Checks that cin first 3 digits are the same for the dossier identified using the unique_identifier attribute
        Be Careful! "unique_identifier" not be confused wth "id"

        """
        dossier = (
            self.model.objects.filter(
                municipality_id=kwargs["municipality_id"],
                unique_identifier=serializer.validated_data["unique_identifier"],
            )
            .order_by("created_at")
            .last()
        )
        if dossier is None:
            return Response(
                data={"message": "id does not exist"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if dossier.cin_number[-3:] != serializer.validated_data["cin_digits"]:
            return Response(
                data={"message": "incorrect cin digits"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        dossier.followers.add(request.user)
        dossier.save()
        return Response(
            data=dossier.to_dict(),
            status=status.HTTP_202_ACCEPTED,
        )

    def get(self, request, **kwargs):
        """
        Returns all followed dossiers
        Be Careful! "unique_identifier" not be confused wth "id"
        """
        data = [
            obj.to_dict()
            for obj in request.user.dossiers.filter(
                municipality_id=kwargs["municipality_id"]
            ).order_by("-id")[:10]
        ]
        return Response(data=data, status=status.HTTP_200_OK)


@IsValidGenericApi()
class FollowComplaintView(GenericAPIView):
    serializer_class = FollowComplaintSerializer
    model = Complaint
    permission_classes = [DefaultPermission]

    def post(self, request, serializer, **kwargs):
        instance = get_object_or_404(
            self.model,
            municipality_id=kwargs["municipality_id"],
            id=serializer.validated_data["id"],
        )
        instance.followers.add(request.user)
        instance.save()
        return Response(
            data=instance.to_dict(),
            status=status.HTTP_202_ACCEPTED,
        )

    def get(self, request, **kwargs):
        data = [
            obj.to_dict()
            for obj in request.user.complaints.filter(
                municipality_id=kwargs["municipality_id"]
            ).order_by("-id")[:10]
        ]
        return Response(data=data, status=status.HTTP_200_OK)


@IsValidGenericApi()
class FollowSubjectAccessRequestView(GenericAPIView):
    serializer_class = FollowSubjectAccessRequestSerializer
    model = SubjectAccessRequest
    permission_classes = [DefaultPermission]

    def post(self, request, serializer, **kwargs):
        instance = get_object_or_404(
            self.model,
            municipality_id=kwargs["municipality_id"],
            id=serializer.validated_data["id"],
        )
        instance.followers.add(request.user)
        instance.save()
        return Response(
            data=SubjectAccessRequestSerializer(instance).data,
            status=status.HTTP_202_ACCEPTED,
        )

    def get(self, request, **kwargs):
        data = [
            SubjectAccessRequestSerializer(obj).data
            for obj in request.user.subject_access_requests.filter(
                municipality_id=kwargs["municipality_id"]
            ).order_by("-id")[:10]
        ]
        return Response(data=data, status=status.HTTP_200_OK)


@IsValidGenericApi()
class FollowCommentView(GenericAPIView):
    serializer_class = FollowCommentSerializer
    model = Comment
    permission_classes = [DefaultPermission]

    def post(self, request, serializer, **kwargs):
        instance = get_object_or_404(
            self.model,
            parent_comment=None,
            municipality_id=kwargs["municipality_id"],
            id=serializer.validated_data["id"],
        )
        instance.followers.add(request.user)
        instance.save()
        return Response(
            data=instance.to_dict(),
            status=status.HTTP_202_ACCEPTED,
        )

    def get(self, request, **kwargs):
        data = [
            obj.to_dict()
            for obj in request.user.comments.filter(
                municipality_id=kwargs["municipality_id"]
            ).order_by("-id")[:10]
        ]
        return Response(data=data, status=status.HTTP_200_OK)
