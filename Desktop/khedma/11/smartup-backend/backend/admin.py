import logging
import os
import time
from datetime import date, timedelta

from celery.result import AsyncResult
from django import forms
from django.contrib import admin, messages
from django.contrib.sites.models import Site
from django.http import FileResponse, HttpResponseRedirect
from django.utils import timezone
from guardian.admin import GuardedModelAdmin

from backend.models import (
    Appointment,
    Association,
    Citizen,
    Comment,
    Committee,
    Complaint,
    ComplaintCategory,
    ComplaintSubCategory,
    Dossier,
    Event,
    Manager,
    Municipality,
    News,
    NewsTag,
    Notification,
    OperationUpdate,
    Procedure,
    Reaction,
    Region,
    RegisteredDevice,
    Report,
    Reservation,
    StaticText,
    SubjectAccessRequest,
    Topic,
)
from backend.serializers.serializers import MunicipalitySerializer
from settings.admin import ExportModelAdmin
from settings.settings import MEDIA_ROOT
from stats.tasks import export_kpis_as_excel

logger = logging.getLogger("default")


class CitizenAdmin(ExportModelAdmin):
    list_display = [
        "__str__",
        "user",
        "birth_date",
        "is_active",
        "date_joined",
        "validation_code",
        "registration_municipality",
        "preferred_municipality",
        "first_login",
        "municipalities_display",
        "gender",
        "is_deleted",
        "id",
    ]
    filter_horizontal = ["municipalities"]
    search_fields = ["id", "user__username", "user__first_name", "user__last_name"]
    list_filter = [
        "user__is_active",
        "registration_municipality__city",
        "registration_municipality",
    ]

    def municipalities_display(self, obj):
        return " | ".join([m.name for m in obj.municipalities.all()])

    municipalities_display.short_description = "Municipalities"


class ManagerAdmin(ExportModelAdmin):
    list_display = [
        "__str__",
        "user",
        "get_email",
        "municipality",
        "title",
        "is_active",
        "last_login",
        "date_joined",
        "id",
    ]
    search_fields = ["id", "user__username", "user__first_name", "user__last_name"]

    def get_email(self, obj):
        return obj.user.email

    get_email.short_description = "email"


class ExportKPIForm(forms.Form):
    created_at = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'datepicker'}),
        input_formats=['%Y-%m-%d'],
    )


class MunicipalityAdmin(GuardedModelAdmin):
    list_display = [
        "__str__",
        "name",
        "name_fr",
        "city",
        "population",
        "is_active",
        "is_signed",
        "has_eticket",
        "managers_count",
        "total_registered",
        "total_starred",
        "total_followed",
        "id",
    ]
    fieldsets = (
        (
            "General Information",
            {
                "fields": (
                    "name",
                    "name_fr",
                    "city",
                    "is_active",
                    "is_signed",
                    "logo",
                    "latitude",
                    "longitude",
                    "activation_date",
                    "contract_signing_date",
                )
            },
        ),
        (
            "Links",
            {
                "fields": (
                    "website",
                    "facebook_url",
                )
            },
        ),
        (
            "Statistics",
            {
                "fields": (
                    "population",
                    "total_sms_consumption",
                    "broadcast_frequency",
                    "last_broadcast",
                    "sms_credit",
                )
            },
        ),
        (
            "Feature",
            {
                "fields": (
                    "service_eticket",
                    "service_dossiers",
                    "service_complaints",
                    "service_sar",
                    "service_procedures",
                    "service_news",
                    "service_forum",
                    "service_reports",
                    "service_events",
                )
            },
        ),
    )
    search_fields = ["id", "name", "name_fr", "city"]
    list_filter = ["is_active", "city"]
    actions = ['export_kpis']
    change_list_template = 'admin/municipality_change_list.html'

    def get_export_kpi_form(self, request):
        return ExportKPIForm(request.POST)

    def export_kpis(self, request, queryset):
        file_path = os.path.join(
            MEDIA_ROOT, "internal", f"latest_kpis_{time.time()}.xlsx"
        )
        try:
            form = self.get_export_kpi_form(request)
            created_at = form.data.get('created_at')
            if not created_at:
                created_at = date.today() - timedelta(days=3 * 30)
            if form.is_valid():
                queryset = queryset.filter(is_active=True)
                serializer = MunicipalitySerializer(queryset, many=True)

                serialized_data = serializer.data
                result = export_kpis_as_excel.delay(
                    serialized_data, created_at, file_path
                )
                task_id = result.task_id
                request.session['export_task_id'] = task_id
                request.session.pop('file_path', None)
                request.session['file_path'] = result.result
        except Exception as e:
            logging.error(f"An exception occurred: {str(e)}")
            messages.error(request, "An error occurred during KPI export.")
        return HttpResponseRedirect(file_path.replace("/backend", ""))

    export_kpis.short_description = "Generate KPI Excel File"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['export_kpi_form'] = self.get_export_kpi_form(request)
        file_path = request.session.pop('file_path', None)
        task_id = request.session.get('export_task_id')

        if task_id:
            task = AsyncResult(task_id)
            if task.ready():
                if task.successful():
                    if file_path and os.path.exists(file_path):
                        file_name = os.path.basename(file_path)
                        response = FileResponse(open(file_path, 'rb'))
                        response[
                            'Content-Disposition'
                        ] = f'attachment; filename="{file_name}"'
                        return response
                    else:
                        extra_context['file_path'] = None
                        extra_context[
                            'file_error'
                        ] = 'The file is not ready for download.'
                else:
                    extra_context[
                        'file_error'
                    ] = 'There was an error generating the file.'
        return super().changelist_view(request, extra_context=extra_context)


class CreatedByModelAdmin(ExportModelAdmin):
    def created_by_user_name(self, obj):
        return obj.created_by.get_full_name()

    created_by_user_name.short_description = "CREATED BY"


class ComplaintsAdmin(CreatedByModelAdmin):
    list_filter = ["is_public", "created_at", "municipality"]
    list_display = [
        "id",
        "municipality",
        "created_by_user_name",
        "problem_summary",
        "address",
        "status",
        "is_public",
        "region",
        "category",
        "sub_category",
        "created_at",
        "hits_count",
    ]
    search_fields = ["id", "problem", "solution", "address"]

    def problem_summary(self, obj):
        return obj.problem[:50]


class RegionAdmin(ExportModelAdmin):
    list_filter = ["municipality"]
    list_display = ["__str__", "municipality", "name", "id"]


class ComplaintCategoryAdmin(ExportModelAdmin):
    list_display = ["name", "id"]


class ComplaintSubCategoryAdmin(ExportModelAdmin):
    list_display = ["__str__", "category", "name", "id"]


class SubjectAccessRequestAdmin(CreatedByModelAdmin):
    list_filter = ["is_public", "municipality"]
    list_display = [
        "__str__",
        "municipality",
        "created_by_user_name",
        "status",
        "is_public",
        "created_at",
        "id",
    ]
    search_fields = ["id", "problem", "solution", "address"]


class NewsAdmin(CreatedByModelAdmin):
    list_filter = ["published_at", "municipality"]
    list_display = [
        "__str__",
        "municipality",
        "title",
        "hits_count",
        "likes_count",
        "id",
    ]
    search_fields = ["id", "title"]

    def likes_count(self, obj):
        return obj.reactions.count()


class ProceduresAdmin(CreatedByModelAdmin):
    list_filter = ["municipality", "type"]
    list_display = ["__str__", "municipality", "title", "type", "id"]
    search_fields = ["id", "title", "type"]

    def problem_summary(self, obj):
        return obj.problem[:50]


class DossiersAdmin(ExportModelAdmin):
    list_filter = ["municipality", "type"]
    list_display = [
        "id",
        "municipality",
        "name",
        "type",
        "status",
        "unique_identifier",
        "deposit_date",
        "created_at",
        "followers_count",
    ]
    search_fields = ["id", "name", "unique_identifier"]

    def followers_count(self, obj):
        return obj.followers.count()

    followers_count.short_description = "FOLLOWERS_COUNT"


class CommitteeAdmin(ExportModelAdmin):
    list_filter = ["municipality"]
    list_display = ["__str__", "municipality", "title", "body_summary", "id"]

    def body_summary(self, obj):
        # FIXME redundant
        if obj.body is not None:
            return obj.body[:100]
        return ""


class ReportAdmin(ExportModelAdmin):
    list_filter = ["municipality"]
    list_display = ["__str__", "municipality", "title", "committee", "date", "id"]


class ReactionAdmin(ExportModelAdmin):
    list_display = ["__str__", "value", "object_id", "post", "id"]


class CommentAdmin(CreatedByModelAdmin):
    list_filter = [
        "type",
        "topic",
        "municipality",
    ]
    list_display = [
        "__str__",
        "municipality",
        "committee_id",
        "created_by_user_name",
        "status",
        "type",
        "topic",
        "title",
        "body_summary",
        "created_at",
        "id",
    ]

    def body_summary(self, obj):
        if obj.body is not None:
            return obj.body[:100]
        return ""


class RegisteredDeviceAdmin(ExportModelAdmin):
    search_fields = ["id"]
    list_filter = ["last_version"]
    list_display = [
        "__str__",
        "user",
        "owner_name",
        "last_login",
        "device_unique_id",
        "model",
        "model",
        "last_version",
        "os_version",
        "os",
        "id",
    ]


class EventAdmin(ExportModelAdmin):
    list_filter = ["starting_date", "ending_date", "municipality"]
    list_display = [
        "__str__",
        "municipality",
        "title",
        "starting_date",
        "ending_date",
        "interested_count",
        "participants_count",
        "id",
    ]

    def interested_count(self, obj):
        return obj.interested_citizen.count()

    def participants_count(self, obj):
        return obj.participants.count()


class AssociationAdmin(ExportModelAdmin):
    list_display = ["__str__", "full_name", "full_name_arabic", "logo", "id"]


class StaticTextAdmin(ExportModelAdmin):
    list_display = ["__str__", "title", "id"]


class AppointmentAdmin(CreatedByModelAdmin):
    list_display = [
        "__str__",
        "host",
        "created_at",
        "starting_date",
        "ending_date",
        "is_published",
        "reservations_made",
        "max_reservations",
        "suggested_by",
        "id",
    ]


class ReservationAdmin(CreatedByModelAdmin):
    list_display = [
        "__str__",
        "title",
        "created_at",
        "reservation_state_citizen",
        "status",
    ]


class NewsTagAdmin(CreatedByModelAdmin):
    list_display = ["name"]


class TopicCommentAdmin(CreatedByModelAdmin):
    list_display = [
        "__str__",
        "label",
        "municipality",
        "state",
        "description",
        "created_at",
    ]


class OperationUpdateAdmin(CreatedByModelAdmin):
    list_display = [
        "__str__",
        "created_at",
        "content_type",
        "object_id",
        "status",
        "get_municipality",
        "get_created_by",
    ]
    list_filter = ["status"]

    def get_municipality(self, obj):
        try:
            return obj.operation.municipality
        except AttributeError:
            return "No Municipality"

    def get_created_by(self, obj):
        try:
            return obj.created_by.first_name + " " + obj.created_by.last_name
        except AttributeError:
            return "No Manager"

    get_created_by.short_description = "CREATED_BY"
    get_municipality.short_description = "MUNICIPALITY"


models = [
    (Citizen, CitizenAdmin),
    (Manager, ManagerAdmin),
    (SubjectAccessRequest, SubjectAccessRequestAdmin),
    (Complaint, ComplaintsAdmin),
    (Region, RegionAdmin),
    (ComplaintCategory, ComplaintCategoryAdmin),
    (ComplaintSubCategory, ComplaintSubCategoryAdmin),
    (Dossier, DossiersAdmin),
    (Report, ReportAdmin),
    (Procedure, ProceduresAdmin),
    (Association, AssociationAdmin),
    (Municipality, MunicipalityAdmin),
    (Committee, CommitteeAdmin),
    (Comment, CommentAdmin),
    (News, NewsAdmin),
    (Reaction, ReactionAdmin),
    (Event, EventAdmin),
    (StaticText, StaticTextAdmin),
    (RegisteredDevice, RegisteredDeviceAdmin),
    (OperationUpdate, OperationUpdateAdmin),
    (Appointment, AppointmentAdmin),
    (Reservation, ReservationAdmin),
    (NewsTag, NewsTagAdmin),
    (Topic, TopicCommentAdmin),
]

for model, model_class in models:
    admin.site.register(model, model_class)

admin.site.unregister(Site)
admin.site.site_header = "elBaladiya.tn البلدية الرقمية"
admin.site.site_title = "elBaladiya.tn البلدية الرقمية"
