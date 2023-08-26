from django.contrib import admin

from etickets.models import Agency, Reservation
from settings.admin import ExportModelAdmin


class AgencyAdmin(ExportModelAdmin):
    list_display = [
        "__str__",
        "name",
        "municipality",
        "base_url",
        "num_agency",
        "is_active",
        "id",
    ]
    search_fields = ["municipality"]
    list_filter = ["is_active"]


class ReservationAdmin(ExportModelAdmin):
    list_display = [
        "__str__",
        "agency",
        "created_by",
        "service_name",
        "created_at",
        "is_active",
        "id",
    ]
    search_fields = ["municipality", "service_name"]
    list_filter = ["service_name"]


models = [
    (Agency, AgencyAdmin),
    (Reservation, ReservationAdmin),
]

for model, model_class in models:
    admin.site.register(model, model_class)
