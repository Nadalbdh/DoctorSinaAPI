from django.contrib import admin
from django.db.models import Count
from django.utils.translation import gettext_lazy as _

from api_logger.models import APILog
from settings.admin import ExportModelAdmin


class APILogsAdmin(ExportModelAdmin):
    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.DRF_API_LOGGER_SLOW_API_ABOVE = None

    def timestamp(self, obj):
        return obj.timestamp.strftime("%d %b %Y %H:%M:%S")

    timestamp.admin_order_field = "created_at"
    timestamp.short_description = "Created at"

    list_per_page = 20
    list_display = (
        "id",
        "user",
        "api_url",
        "method",
        "status_code",
        "execution_time",
        "timestamp",
    )
    list_filter = (
        "timestamp",
        "status_code",
        "method",
    )
    search_fields = (
        "body",
        "api_url",
    )
    readonly_fields = (
        "execution_time",
        "client_ip",
        "api_url",
        "body",
        "method",
        "status_code",
        "timestamp",
    )
    exclude = ("timestamp",)

    change_list_template = "change_list.html"
    date_hierarchy = "timestamp"

    def changelist_view(self, request, extra_context=None):
        response = super(APILogsAdmin, self).changelist_view(request, extra_context)
        try:
            filtered_query_set = response.context_data["cl"].queryset
        except AttributeError:
            return response
        analytics_model = (
            filtered_query_set.values("timestamp__date")
            .annotate(total=Count("id"))
            .order_by("total")
        )
        status_code_count_mode = (
            filtered_query_set.values("id")
            .values("status_code")
            .annotate(total=Count("id"))
            .order_by("status_code")
        )
        status_code_count_keys = list()
        status_code_count_values = list()
        for item in status_code_count_mode:
            status_code_count_keys.append(item.get("status_code"))
            status_code_count_values.append(item.get("total"))
        extra_context = dict(
            analytics=analytics_model,
            status_code_count_keys=status_code_count_keys,
            status_code_count_values=status_code_count_values,
        )
        response.context_data.update(extra_context)
        return response

    def get_queryset(self, request):
        return super(APILogsAdmin, self).get_queryset(request)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(APILog, APILogsAdmin)
