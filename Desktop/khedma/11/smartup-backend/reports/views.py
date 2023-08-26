from datetime import timedelta

from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_401_UNAUTHORIZED
from rest_framework.views import APIView
from rest_framework_simplejwt.backends import TokenBackend
from rest_framework_simplejwt.exceptions import TokenBackendError

from backend.decorators import IsValidGenericApi
from backend.enum import MunicipalityPermissions, RequestStatus
from backend.functions import is_municipality_manager
from backend.helpers import get_managers_by_permission_per_municipality
from backend.models import (
    Complaint,
    ComplaintCategory,
    Municipality,
    SubjectAccessRequest,
)


class PDFReportMixin:
    template_name = None
    manager_permission = None
    model = None

    def __init__(self):
        super().__init__()
        self.bearer = None
        self.status = None
        self.start = None
        self.end = None
        self.interval = (None, None)
        self.user = None
        self.municipality = None

    def get_params(self, request, **kwargs):
        # Params to filter with
        self.bearer = request.GET.get("bearer", "")
        self.status = request.GET.get("status", None)
        self.start = request.GET.get("start", None)
        self.end = request.GET.get("end", None)
        self.municipality = Municipality.objects.get(pk=kwargs["municipality_id"])

    def check_manager_permission(self, **kwargs):
        data = TokenBackend(algorithm="HS256").decode(self.bearer, verify=False)
        self.user = User.objects.get(pk=data["user_id"])
        if not hasattr(self.user, "manager") or not is_municipality_manager(
            self.user, kwargs["municipality_id"]
        ):
            raise PermissionDenied()

        managers = get_managers_by_permission_per_municipality(
            self.municipality, self.manager_permission
        )

        if not self.user.manager in managers:
            raise PermissionDenied()

    def default_filter_queryset(self):
        q_objects = Q(
            municipality=self.municipality,
        )
        if (
            isinstance(self.start, str)
            and isinstance(self.end, str)
            and self.end.count("-") > 3
            and self.start.count("-") > 3
        ):
            start = [int(n) for n in self.start.split("-")]
            end = [int(n) for n in self.end.split("-")]
            self.interval = (
                timezone.datetime(start[0], start[1], start[2]),
                timezone.datetime(end[0], end[1], end[2]),
            )
            q_objects.add(Q(created_at__range=self.interval), Q.AND)

        if self.status and (
            self.status in [status[0] for status in RequestStatus.get_choices()]
        ):
            q_objects.add(Q(last_status=self.status), Q.AND)
        return q_objects

    def get_context(self, query):
        return {
            "objects": query,
            "start": self.interval[0] if hasattr(self, "interval") else None,
            "end": self.interval[1] if hasattr(self, "interval") else None,
            "municipality": self.municipality,
            "status": self.status,
        }

    def get(self, request, *args, **kwargs):
        try:
            return self.make_template(request, *args, **kwargs)
        except TokenBackendError:
            return Response({"message": "Not Authorized"}, status=HTTP_401_UNAUTHORIZED)
        except PermissionDenied:
            return Response(
                {
                    "message": f"You must be a manager in the specified municipality to access this resource"
                },
                status=HTTP_401_UNAUTHORIZED,
            )
        except Exception as e:
            return Response({"message": f"{e}"}, status=HTTP_401_UNAUTHORIZED)

    def make_template(self) -> HttpResponse:
        pass


@IsValidGenericApi()
class PDFComplaintReport(APIView, PDFReportMixin):
    template_name = "complaints_report.html"
    manager_permission = MunicipalityPermissions.MANAGE_COMPLAINTS
    permission_classes = [AllowAny]
    model = Complaint

    def __init__(self):
        super().__init__()
        self.category = None

    def get_params(self, request, **kwargs):
        super().get_params(request, **kwargs)
        category = request.GET.get("category", None)
        # Checks whether the value category can be converted to an integer if not then category=none
        if category:
            try:
                self.category = int(category)
            except ValueError:
                self.category = None
        else:
            self.category = None

    def make_template(self, request, *args, **kwargs):
        self.get_params(request, **kwargs)

        if self.category:
            self.category = ComplaintCategory.objects.get(pk=self.category)
        # Check for manager permission
        self.check_manager_permission(**kwargs)

        q_objects = self.default_filter_queryset()
        if self.category:
            q_objects.add(Q(category=self.category), Q.AND)

        query = self.model.objects.filter(q_objects)
        context = self.get_context(query)
        context["category"] = self.category

        return render(request, self.template_name, context)


@IsValidGenericApi()
class PDFSubjectAccessReport(APIView, PDFReportMixin):
    template_name = "sars_report.html"
    manager_permission = MunicipalityPermissions.MANAGE_SUBJECT_ACCESS_REQUESTS
    permission_classes = [AllowAny]
    model = SubjectAccessRequest

    def make_template(self, request, *args, **kwargs):
        self.get_params(request, **kwargs)
        self.check_manager_permission(**kwargs)
        q_objects = self.default_filter_queryset()
        query = self.model.objects.filter(q_objects)
        context = self.get_context(query)
        return render(request, self.template_name, context)
