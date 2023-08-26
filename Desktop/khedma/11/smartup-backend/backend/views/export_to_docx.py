from datetime import date
from os import path

from rest_framework.views import APIView

from backend.exceptions import NotOwner
from backend.functions import is_municipality_manager
from backend.mixins import ExportedToDocxMixin
from backend.models import SubjectAccessRequest
from settings.custom_permissions import DefaultPermission
from settings.settings import DOCX_TEMPLATES_PATH, MEDIA_ROOT


class ExportSubjectAccessRequestToDocxView(APIView, ExportedToDocxMixin):
    permission_classes = [DefaultPermission]

    model = SubjectAccessRequest

    template = f"{DOCX_TEMPLATES_PATH}/subject_access_request_template"
    file_prefix = "access_request_to"

    def get_context(self, user, id, *args, **kwargs):
        instance = self.model.objects.select_related("created_by").get(pk=id)
        if not instance.created_by == user and not is_municipality_manager(
            user, kwargs.get("municipality_id", None)
        ):
            raise NotOwner

        is_on_place = "✘" if instance.on_spot_document else " "
        is_e_doc = "✘" if instance.electronic_document else " "
        is_printed_document = "✘" if instance.printed_document else " "
        is_part_document = "✘" if instance.parts_of_document else " "
        ctx = {
            "fax": " ",
            "identifier_number": instance.created_by.citizen.cin_number
            if instance.created_by.citizen.cin_number
            else "",
            "first_name": instance.created_by.first_name,
            "last_name": instance.created_by.last_name,
            "email": instance.created_by.email if instance.created_by.email else "",
            "phone": instance.created_by.username,
            "address": instance.created_by.citizen.address
            if instance.created_by.citizen.address
            else "",
            "document": instance.document if instance.document else "",
            "is_simple_user": True,
            "is_on_place": is_on_place,
            "is_e_doc": is_e_doc,
            "is_part_document": is_part_document,
            "is_printed_document": is_printed_document,
            "reference": instance.reference if instance.reference else "",
            "structure": instance.structure if instance.structure else "",
            "date": instance.created_at.strftime("%d/%m/%Y"),
        }
        return ctx

    def get_document_path(self, file_name: str) -> str:
        return path.join(
            MEDIA_ROOT, "subject-access-requests", "files", f"{file_name}.docx"
        )
