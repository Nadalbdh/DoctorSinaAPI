from django.contrib import admin

from etickets_v2.models import Agency, Reservation, Service
from settings.admin import ExportModelAdmin


class CreatedByModelAdmin(ExportModelAdmin):
    def created_by_user_name(self, obj):
        return obj.created_by.get_full_name()

    created_by_user_name.short_description = "CREATED BY"


class ServicesAdmin(CreatedByModelAdmin):
    list_filter = ["created_at"]
    list_display = ["__str__", "agency", "name", "id", "created_at", "description"]


class AgenciesAdmin(CreatedByModelAdmin):
    list_filter = ["created_at", "municipality"]
    list_display = [
        "__str__",
        "municipality",
        "is_active",
        "name",
        "local_ip",
    ]


class EReservationAdmin(CreatedByModelAdmin):
    list_filter = ["created_at", "service"]
    list_display = ["__str__"]


models = [
    (Service, ServicesAdmin),
    (Agency, AgenciesAdmin),
    (Reservation, EReservationAdmin),
]

for model, model_class in models:
    admin.site.register(model, model_class)
