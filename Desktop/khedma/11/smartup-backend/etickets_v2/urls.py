from django.urls import include, path

from etickets_v2.routers import CustomRouter
from etickets_v2.views import (
    AgenciesView,
    EticketScoringView,
    LocalReservationsView,
    ReservationsView,
    ServicesView,
)

app_name = "etickets_v2"
agency_router = CustomRouter()
agency_router.register(r"agencies", AgenciesView, basename=AgenciesView.basename)

service_router = CustomRouter()
service_router.register(r"services", ServicesView, basename=ServicesView.basename)

reservation_router = CustomRouter()
reservation_router.register(
    r"reservations", ReservationsView, basename=ReservationsView.basename
)


urlpatterns = agency_router.urls + [
    path("agencies/<str:agency>/", include(service_router.urls)),
    path("agencies/<str:agency>/", include(reservation_router.urls)),
    path(
        "agencies/convert-physical-ticket",
        LocalReservationsView.as_view(),
        name="convert-physical-ticket",
    ),
    path(
        "agency/choose-best",
        EticketScoringView.as_view(),
        name="eticket-scoring",
    ),
]
