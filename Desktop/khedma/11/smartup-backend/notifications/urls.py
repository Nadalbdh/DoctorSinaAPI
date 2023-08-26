from django.urls import path

from . import views
from .views import (
    FollowCommentView,
    FollowComplaintView,
    FollowDossierView,
    FollowSubjectAccessRequestView,
)

app_name = "notifications"

urlpatterns = [
    path("", views.NotificationsView.as_view(), name="get_all_notifications"),
    path(
        "mark-as-read",
        views.AllNotificationsReadView.as_view(),
        name="mark_notifications_as_read",
    ),
    path("<int:id>", views.NotificationView.as_view(), name="get_notification"),
    path(
        "<int:id>/mark-as-read",
        views.MarkNotificationRead.as_view(),
        name="mark_single_notification_as_read",
    ),
    path(
        "municipalities/<int:municipality_id>/dossiers/follow",
        FollowDossierView.as_view(),
        name="dossiers-follow",
    ),
    path(
        "municipalities/<int:municipality_id>/complaints/follow",
        FollowComplaintView.as_view(),
        name="complaints-follow",
    ),
    path(
        "municipalities/<int:municipality_id>/subject-access-requests/follow",
        FollowSubjectAccessRequestView.as_view(),
        name="subject-access-requests-follow",
    ),
    path(
        "municipalities/<int:municipality_id>/forum/comments/follow",
        FollowCommentView.as_view(),
        name="comments-follow",
    ),
]
