from django.urls import path
from rest_framework.routers import DefaultRouter

from stats.views import KPIView, SignMetabaseEmbed, StatsView, StatsViewPerDate

app_name = "stats"
router = DefaultRouter()

urlpatterns = router.urls + [
    path("all", StatsView.as_view()),
    path("<int:year>", StatsViewPerDate.as_view()),
    path("dashboard/<int:dashboard_id>", SignMetabaseEmbed.as_view(), name="dashboard"),
    path(
        "municipalities/<int:municipality_id>", KPIView.as_view(), name="municipality"
    ),
]
