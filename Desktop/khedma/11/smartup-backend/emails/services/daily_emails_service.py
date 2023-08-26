from datetime import date, timedelta

from django.db.models import Count, Q
from django.utils import timezone

from backend.enum import MunicipalityPermissions
from backend.helpers import get_frontend_url
from backend.models import Comment, Complaint, SubjectAccessRequest
from emails.models import Email
from emails.services import PerCollectionEMailService
from emails.services.mixins import PermissionBasedRecipientsMixin
from settings.settings import BACK_OFFICE_URL


class DailyEmailService(PermissionBasedRecipientsMixin, PerCollectionEMailService):
    def __init__(self, municipality, time_span):
        self.municipality = municipality
        self.time_span = time_span
        self.start_date = timezone.now() - timedelta(hours=self.time_span + 1)

    @property
    def today(self):
        return date.today().strftime("%d/%m/%Y")


class DailySubjectAccessRequestEmail(DailyEmailService):
    template = "email_subject_access_request_template.html"
    permission = MunicipalityPermissions.MANAGE_SUBJECT_ACCESS_REQUESTS

    def get_subject(self, mobj):
        return f"التقرير اليومي لمطالب النفاذ للمعلومة الواردة ل{self.municipality.name} بتاريخ {self.today}"

    def get_template_params(self, mobj):
        return {
            "municipality": self.municipality,
            "base_url": BACK_OFFICE_URL + "/pages/acces-info/edit/",
            "objects": mobj,
            "count": mobj.count(),
            "hours": self.time_span,
        }

    def get_mail_object(self):
        return SubjectAccessRequest.objects.filter(
            created_at__gte=self.start_date, municipality=self.municipality
        )


class DailyComplaintEmail(DailyEmailService):
    template = "email_complaint_template.html"
    permission = MunicipalityPermissions.MANAGE_COMPLAINTS

    def get_subject(self, mobj):
        return f"التقرير اليومي للتبليغات الرقمية الواردة ل{self.municipality.name} بتاريخ {self.today}"

    def get_template_params(self, mobj):
        return {
            "municipality": self.municipality,
            "base_url": BACK_OFFICE_URL + "/pages/complaint/edit/",
            "objects": mobj,
            "count": mobj.count(),
            "hours": self.time_span,
        }

    def get_mail_object(self):
        return Complaint.objects.filter(
            created_at__gte=self.start_date, municipality=self.municipality
        )


class DailyForumEMail(DailyEmailService):
    template = "email_forum_summary.html"

    def __init__(self, municipality):
        super().__init__(municipality, 24)

    def get_subject(self, mobj):
        return f"التقرير اليومي للمقترحات الواردة ل{self.municipality.name} بتاريخ {self.today}"

    def get_mail_object(self):
        posts_with_recent_comments = Comment.posts.annotate(
            count_recent=Count(
                "sub_comments", filter=Q(created_at__gte=self.start_date)
            ),
        ).filter(count_recent__gt=0, municipality=self.municipality)

        return {
            "posts": Comment.posts.filter(
                municipality=self.municipality, created_at__gte=self.start_date
            ),
            "interactions": posts_with_recent_comments,
        }

    def get_recipients(self):
        return [e.email for e in Email.objects.filter(municipality=self.municipality)]

    def get_template_params(self, mobj):
        return {
            "municipality": self.municipality,
            "base_url": f"{get_frontend_url(self.municipality)}/forum/",
            "objects": mobj,
            "comments_number": mobj["posts"].count(),
        }

    def should_send(self, mobj, recipients):
        return recipients and (mobj["posts"] or mobj["interactions"])
