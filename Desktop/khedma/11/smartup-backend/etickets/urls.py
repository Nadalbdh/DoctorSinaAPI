from django.urls import include, path

from backend.routers import CustomCRUDRouter
from etickets.views import (
    AgencyViewSet,
    GetCurrentReservation,
    MyETicketPDF,
    ReservationViewSet,
    TicketNotificationView,
)

app_name = "etickets"
crud_router = CustomCRUDRouter()
crud_router.register(r"reservations", ReservationViewSet, basename="reservation")
router = CustomCRUDRouter()
router.register(r"", AgencyViewSet, basename="agency")

urlpatterns = [
    path(
        "notifications-refresh/", TicketNotificationView.as_view(), name="notifications"
    ),
    path("agencies/<int:agency>/", include(crud_router.urls)),
    path("", include(router.urls)),
    path(
        "agencies/<int:agency_id>/current_reservation",
        GetCurrentReservation.as_view(),
        name="current_reservation",
    ),
    path(
        "agencies/<int:agency_id>/ticket/<int:service>",
        MyETicketPDF.as_view(),
        name="my_eticket",
    ),
]
