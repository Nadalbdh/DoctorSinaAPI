from datetime import timedelta

from django.utils import timezone

from backend.enum import MunicipalityPermissions, RequestStatus
from backend.models import Complaint, Dossier, SubjectAccessRequest
from emails.services import OneObjectEMailService, PerObjectEMailService
from emails.services.mixins import PermissionBasedRecipientsMixin
from emails.utils import get_sender_email_for
from settings.settings import COMPLAINT_URL, DOSSIER_URL, SUBJECT_ACCESS_REQUEST_URL

SENDER = get_sender_email_for("notifications")


class ConfigurationEmailService(PermissionBasedRecipientsMixin):
    base_url = None
    model = None
    status = None
    wants_update = False

    def __init__(self, municipality, days, message):
        self.municipality = municipality
        self.days = days
        self.message = message
        self.today = timezone.now()
        unchanged_for_x_days = days
        start_day = (
            self.today - timedelta(days=unchanged_for_x_days + 1) + timedelta(hours=1)
        )
        end_day = start_day + timedelta(days=1)
        self.interval = (start_day, end_day)

    def get_template_params(self, mobj):
        return {
            "municipality": self.municipality,
            "base_url": self.base_url,
            "object": mobj,  # We are sending an email per "object"
            # updated we can send many object per mail with PerObjectEMailService
            "nb_days": self.days,
        }

    def get_mail_object(self):
        """
        Fetch model having status status ranging between 2 {dates}
        """
        objects = self.model.objects.filter(
            municipality=self.municipality, last_status=self.status
        )
        if self.wants_update:
            return objects.filter(last_update__range=self.interval)
        return objects.filter(created_at__range=self.interval)


class ReminderComplaintReceivedEmail(ConfigurationEmailService, OneObjectEMailService):
    """
    Send all received complaints for each configuration in one mail
    """

    template = "email_complaint_received_template.html"
    base_url = COMPLAINT_URL
    permission = MunicipalityPermissions.MANAGE_COMPLAINTS
    model = Complaint
    status = RequestStatus.RECEIVED
    wants_update = False

    def get_subject(self, mobj):
        if len(mobj) > 1:
            return f"تذكير {self.message} بورود تشكيات بلدية  {self.municipality.name} "
        else:
            return f"تذكير {self.message} بورود لمشكل بلدية  {self.municipality.name} "


class ReminderComplaintProcessingEmail(
    ConfigurationEmailService, OneObjectEMailService
):
    """
    Send all Processing complaints for each configuration in one mail
    """

    template = "email_complaint_process_template.html"
    base_url = COMPLAINT_URL
    permission = MunicipalityPermissions.MANAGE_COMPLAINTS

    model = Complaint
    status = RequestStatus.PROCESSING
    wants_update = True

    def get_subject(self, mobj):
        if len(mobj) > 1:
            return (
                f"تذكير {self.message} بتحيين تشكيات بلدية  {self.municipality.name} "
            )
        else:
            return f"تذكير {self.message} بتحيين للمشكل  بلدية {self.municipality.name}"


class ReminderSubjectAccessReceivedEmail(
    ConfigurationEmailService, PerObjectEMailService
):
    template = "email_subject_access_received_template.html"
    base_url = SUBJECT_ACCESS_REQUEST_URL
    permission = MunicipalityPermissions.MANAGE_SUBJECT_ACCESS_REQUESTS
    model = SubjectAccessRequest
    status = RequestStatus.RECEIVED
    wants_update = False

    def get_subject(self, mobj):
        return (
            f"تذكير {self.message} بورود مطلب نفاذ إلى المعلومة '{mobj.document[:40]}'"
        )


class ReminderDossierProcessingEmail(ConfigurationEmailService, PerObjectEMailService):
    template = "email_dossier_process_template.html"
    base_url = DOSSIER_URL
    permission = MunicipalityPermissions.MANAGE_DOSSIERS
    model = Dossier
    status = RequestStatus.PROCESSING
    wants_update = True

    def get_subject(self, mobj):
        return f"تذكير {self.message} بتحديث وضعية مطلب الرخصة '{mobj.name[:40]}'"
