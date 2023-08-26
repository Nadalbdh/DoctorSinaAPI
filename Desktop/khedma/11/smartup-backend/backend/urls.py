from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt import views as jwt_views

from backend.jwt import CitizenLoginView, ManagerLoginView
from backend.routers import CustomCRUDRouter
from backend.views import (
    ActivateMunicipalityView,
    AppointmentViewSet,
    AssociationsView,
    AssociationView,
    AttachmentViewSet,
    BuildingViewSet,
    ChangePassword,
    CommentsView,
    CommentUpdateStatusView,
    CommentView,
    CommitteesView,
    CommitteeView,
    ComplaintCategoriesView,
    ComplaintCategoriesView_Deprecated,
    ComplaintCategoryView,
    ComplaintCategoryView_Deprecated,
    ComplaintViewSet,
    DossierAttachmentViewSet,
    DossierViewSet,
    EventDisinterestView,
    EventInterestView,
    EventParticipateView,
    EventsView,
    EventUnparticipateView,
    EventView,
    FeedView,
    GetProfilePictureView,
    GetStatusLabeling,
    ManagerChangePasswordView,
    ManagersView,
    ManagerView,
    MunicipalitiesView,
    MunicipalityFollowView,
    MunicipalityMeta,
    MunicipalityOnboardingView,
    MunicipalityUnFollowView,
    MunicipalityView,
    NewsObjectView,
    NewsTagsView,
    NewsTagView,
    NewsView,
    ProceduresView,
    ProcedureView,
    ProfileView,
    ReactionsView,
    RegionsView,
    RegionView,
    RegisterVerifyOTPV2View,
    RegisterVerifyOTPView,
    RegisterView,
    ReportsView,
    ReportView,
    ReservationStatusView,
    ReservationViewSet,
    ResetPassword,
    ResetPasswordVerifyOTP,
    SMSBroadcastRequestReviewView,
    SMSBroadcastRequestViewSet,
    SMSBroadcastView,
    StaticTextsView,
    StaticTextView,
    SubjectAccessRequestViewSet,
    TopicViewSet,
    UpdateMunicipalityFeature,
)
from backend.views.delete_account import DeleteAccount, DeleteManagerAccount
from backend.views.export_to_docx import ExportSubjectAccessRequestToDocxView
from backend.views.healthcheck import HealthCheckView
from backend.views.manager_views import (
    ManagerResetPassword,
    ManagerResetPasswordVerifyOTP,
)
from backend.views.operation_update_views import OperationUpdateViewSet
from etickets_v2.views import GetAllAgenciesView
from settings.settings import DEBUG

app_name = "backend"
urlpatterns = [
    # Registration & Authentication urls
    path("register", RegisterView.as_view(), name="register"),
    path("register/verify-otp", RegisterVerifyOTPView.as_view(), name="verify_otp"),
    path("register/verify-otp/v2", RegisterVerifyOTPV2View.as_view()),
    path("register/update-info", ProfileView.as_view()),
    path("profile", ProfileView.as_view(), name="profile"),
    path("login", CitizenLoginView.as_view(), name="login"),
    path("token/refresh", jwt_views.TokenRefreshView.as_view()),
    path("reset-password", ResetPassword.as_view(), name="reset_password"),
    path(
        "reset-password/verify",
        ResetPasswordVerifyOTP.as_view(),
        name="reset_password_verify",
    ),
    path("change-password", ChangePassword.as_view()),
    # Citizen API endpoint
    path("users/<int:id>/profile-picture", GetProfilePictureView.as_view()),
    # Municipality Getters
    path("municipalities", MunicipalitiesView.as_view(), name="municipalities"),
    # path('municipalities/summary', MunicipalitiesSummary.as_view(), name='municipalities-summary'),
    path(
        "municipalities/<int:municipality_id>",
        MunicipalityView.as_view(),
        name="municipality",
    ),
    path(
        "municipalities/meta/<str:municipality_route_name>",
        MunicipalityMeta.as_view(),
        name="municipality-meta",
    ),
    path(
        "municipalities/features/<int:municipality_id>",
        UpdateMunicipalityFeature.as_view({"put": "partial_update"}),
        name="municipality-feature",
    ),
    path(
        "municipalities/<int:id>/follow",
        MunicipalityFollowView.as_view(),
        name="municipalities-follow",
    ),
    path(
        "municipalities/<int:id>/unfollow",
        MunicipalityUnFollowView.as_view(),
        name="municipalities-unfollow",
    ),
    path(
        "activate-municipality",
        ActivateMunicipalityView.as_view(),
        name="activate-municipality",
    ),
    path(
        "sms-broadcast-request-review",
        SMSBroadcastRequestReviewView.as_view(),
        name="sms-broadcast-request-review",
    ),
    path("sms-broadcast", SMSBroadcastView.as_view(), name="sms-broadcast"),
    path(
        "onboard-municipality",
        MunicipalityOnboardingView.as_view(),
        name="onboard-municipality",
    ),
    # Committee CRUD
    path(
        "municipalities/<int:municipality_id>/committees",
        CommitteesView.as_view(),
        name="committees",
    ),
    path(
        "municipalities/<int:municipality_id>/committees/<int:id>",
        CommitteeView.as_view(),
        name="committee",
    ),
    # Report CRUD
    path("municipalities/<int:municipality_id>/reports", ReportsView.as_view()),
    path("municipalities/<int:municipality_id>/reports/<int:id>", ReportView.as_view()),
    # Procedure CRUD
    path(
        "municipalities/<int:municipality_id>/procedures",
        ProceduresView.as_view(),
        name="procedures",
    ),
    path(
        "municipalities/<int:municipality_id>/procedures/<int:id>",
        ProcedureView.as_view(),
        name="procedure",
    ),
    # News CRUD
    path(
        "municipalities/<int:municipality_id>/news", NewsView.as_view(), name="newss"
    ),  # Yes, I know
    path(
        "municipalities/<int:municipality_id>/news/<int:id>",
        NewsObjectView.as_view(),
        name="news",
    ),
    # Event CRUD
    path("municipalities/<int:municipality_id>/events", EventsView.as_view()),
    path(
        "municipalities/<int:municipality_id>/events/<int:id>",
        EventView.as_view(),
        name="event",
    ),
    path(
        "municipalities/<int:municipality_id>/events/<int:id>/participate",
        EventParticipateView.as_view(),
        name="participate",
    ),
    # DEPRECATED, use participate endpoint with "participate":False instead
    path(
        "municipalities/<int:municipality_id>/events/<int:id>/unparticipate",
        EventUnparticipateView.as_view(),
        name="unparticipate",
    ),
    path(
        "municipalities/<int:municipality_id>/events/<int:id>/interest",
        EventInterestView.as_view(),
        name="interest",
    ),
    # DEPRECATED, use interest endpoint with "interest":False instead
    path(
        "municipalities/<int:municipality_id>/events/<int:id>/disinterest",
        EventDisinterestView.as_view(),
        name="disinterest",
    ),
    # Region CRUD
    path("municipalities/<int:municipality_id>/regions", RegionsView.as_view()),
    path("municipalities/<int:municipality_id>/regions/<int:id>", RegionView.as_view()),
    # Complaint Category CRUD - Deprecated
    path(
        "municipalities/<int:municipality_id>/categories",
        ComplaintCategoriesView_Deprecated.as_view(),
    ),
    path(
        "municipalities/<int:municipality_id>/categories/<int:id>",
        ComplaintCategoryView_Deprecated.as_view(),
    ),
    # Complaint Category CRUD
    path("municipalities/categories", ComplaintCategoriesView.as_view()),
    path("municipalities/categories/<int:id>", ComplaintCategoryView.as_view()),
    # Comment CRUD
    path(
        "municipalities/<int:municipality_id>/forum/comments",
        CommentsView.as_view(),
        name="comments",
    ),
    # replaces /topics url
    path(
        "municipalities/<int:municipality_id>/forum/comments/<int:id>",
        CommentView.as_view(),
        name="comment",
    ),  # replaces /topics url
    path(
        "municipalities/<int:municipality_id>/forum/comments/<int:id>/update",
        CommentUpdateStatusView.as_view(),
        name="comment-status",
    ),
    # Reactions
    path("reactions", ReactionsView.as_view(), name="reactions"),
    # Associations Getters
    path("associations", AssociationsView.as_view(), name="associations"),
    path("associations/<int:id>", AssociationView.as_view(), name="association"),
    # Feed getter
    path("municipalities/<int:municipality_id>/feed", FeedView.as_view(), name="feeds"),
    # Static Texts Getters
    path("static-texts", StaticTextsView.as_view(), name="static-texts"),
    path("static-texts/<str:topic>", StaticTextView.as_view(), name="static-text"),
    # News Tags Getters
    path("news-tags", NewsTagsView.as_view(), name="news-tags"),
    path("news-tags/<str:name>", NewsTagView.as_view(), name="news-tag"),
    # Managers URLS
    path(
        "municipalities/manage/login", ManagerLoginView.as_view(), name="manager_login"
    ),
    path(
        "municipalities/manage/reset-password",
        ManagerResetPassword.as_view(),
        name="manager_reset_password",
    ),
    path(
        "municipalities/manage/reset-password/verify",
        ManagerResetPasswordVerifyOTP.as_view(),
        name="manager_reset_password_verify",
    ),
    path(
        "municipalities/<int:municipality_id>/managers",
        ManagersView.as_view(),
        name="managers",
    ),
    path(
        "municipalities/<int:municipality_id>/managers/<int:user_id>",
        ManagerView.as_view(),
        name="manager",
    ),
    path(
        "municipalities/<int:municipality_id>/managers/<int:user_id>/change-password",
        ManagerChangePasswordView.as_view(),
        name="manager_change_password",
    ),
    # Polls URLS
    path("municipalities/<int:municipality>/", include("polls.urls")),
    # Reservation URL
    path("reservations/<int:id>/update", ReservationStatusView.as_view()),
    # Status labeling
    path("status", GetStatusLabeling.as_view(), name="status"),
    # e-ticket with local server
    path("municipalities/<int:municipality>/", include("etickets_v2.urls")),
    # stats and analytics
    path("stats/", include("stats.urls")),
    path(
        "municipalities/<int:municipality>/operation-updates/<int:id>",
        OperationUpdateViewSet.as_view(),
        name="operation-update",
    ),
    path("delete-account/", DeleteAccount.as_view(), name="delete-account"),
    path(
        "municipalities/<int:municipality_id>/managers/<int:manager_id>/delete-account/",
        DeleteManagerAccount.as_view(),
        name="delete-manager-account",
    ),
    path(
        "municipalities/<int:municipality_id>/subject-access-requests/<int:id>/export-to-docx/",
        ExportSubjectAccessRequestToDocxView.as_view(),
        name="export-sar-docx",
    ),
    path(
        "agencies/",
        GetAllAgenciesView.as_view(),
        name="get-all-agencies",
    ),
    path(
        "health/",
        HealthCheckView.as_view(),
        name="health",
    ),
]

router = DefaultRouter()
router.register(r"appointments", AppointmentViewSet)
router.register(r"attachments", AttachmentViewSet)
router.register(r"reservations", ReservationViewSet, basename="Reservation")
router.register(r"sms-broastcast-request", SMSBroadcastRequestViewSet)

crud_router = CustomCRUDRouter()
crud_router.register(r"topics", TopicViewSet, basename="topic")
crud_router.register(r"complaints", ComplaintViewSet, basename="complaint")
crud_router.register(r"dossiers", DossierViewSet, basename="dossier")
crud_router.register(r"buildings", BuildingViewSet, basename="building")
crud_router.register(
    r"dossiers-attachments", DossierAttachmentViewSet, basename="dossiers-attachment"
)
crud_router.register(
    r"subject-access-requests",
    SubjectAccessRequestViewSet,
    basename="subject-access-request",
)

urlpatterns += [
    path("", include(router.urls)),
    path("municipalities/<int:municipality>/", include(crud_router.urls)),
]

swagger_urls = [
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    # Optional UI:
    path(
        "schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="backend:schema"),
        name="swagger-ui",
    ),
    path(
        "schema/redoc/",
        SpectacularRedocView.as_view(url_name="backend:schema"),
        name="redoc",
    ),
]
# API documentation
if DEBUG == True:
    urlpatterns += swagger_urls
