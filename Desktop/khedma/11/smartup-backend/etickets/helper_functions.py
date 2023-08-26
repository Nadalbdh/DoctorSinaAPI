import logging
from datetime import datetime
from io import BytesIO

import pdfkit
import qrcode
import qrcode.image.svg
import requests
from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from pytz import timezone
from requests.auth import HTTPBasicAuth
from rest_framework.exceptions import NotAcceptable, ValidationError

from etickets.models import Agency

logger = logging.getLogger("default")


class ETicketsHelper:
    """
    TODO No need for a class, separate functions are OK
    This class is a helper for eticket module, it should contain all internal functions related to etickets
    """

    ###########################
    # RESERVATION
    ###########################
    @staticmethod
    def fetch_municipality_api_data(agency_id, reservation=False):
        """
        This function check if the municipality has e-ticket feature available and return need data to make the api
        call
        """
        eticket_data = get_object_or_404(Agency.objects.active(), id=agency_id)
        if reservation:
            ETicketsHelper.check_valid_time(eticket_data)
        return {
            "url": eticket_data.base_url,
            "auth_user": eticket_data.authentication_user,
            "auth_password": eticket_data.authentication_password,
            "num_agency": eticket_data.num_agency,
        }

    @staticmethod
    def _prepare_api_reservation(user, agency_id, service_id):
        """
        Prepare data for the API RESERVATION
        """
        eticket_data = ETicketsHelper.fetch_municipality_api_data(
            agency_id=agency_id, reservation=True
        )
        auth = HTTPBasicAuth(eticket_data["auth_user"], eticket_data["auth_password"])
        data = {
            "id_client": user.id,
            "id_agence": eticket_data["num_agency"],
            "lang": 1,
            "id_service": service_id,
            "token": user.id,
        }
        url = eticket_data["url"] + "reservation"
        return url, data, auth

    @staticmethod
    def process_api_reservation(user, agency_id, service_id):
        url, data, auth = ETicketsHelper._prepare_api_reservation(
            user, agency_id, service_id
        )
        return requests.post(url=url, data=data, auth=auth)

    @staticmethod
    def handle_api_reservation_response(user, agency_id, service_id):
        response = ETicketsHelper.process_api_reservation(user, agency_id, service_id)
        if response.status_code == 201:
            raise NotAcceptable(
                {
                    "error": "You have already reserved for this service, try again later"
                },
                code=406,
            )
        if response.status_code == 200:
            return response.json()
        raise ValidationError(
            {"error": "Fields required or api server not responding"}, code=400
        )

    @staticmethod
    def check_valid_time(agency, serializer=False):
        # Current time in UTC
        now_utc = datetime.now(timezone("UTC"))
        # Convert to Africa/Tunis time zone
        now_tunis = now_utc.astimezone(timezone("Africa/Tunis"))
        if now_tunis.weekday() == 6:
            if serializer:
                return False
            raise ValidationError({"message": "Agency closed on sunday"})
        current_time = now_tunis.time()
        if now_tunis.weekday() == 5:
            if (
                agency.saturday_first_start
                and agency.saturday_first_end
                and agency.saturday_first_start
                <= current_time
                <= agency.saturday_first_end
            ):
                return True
            if (
                agency.saturday_second_start
                and agency.saturday_second_end
                and agency.saturday_second_start
                <= current_time
                <= agency.saturday_second_end
            ):
                return True
            else:
                if serializer:
                    return False
                raise ValidationError(
                    {"message": "Agency closed at this time on saturday"}
                )

        if (
            agency.weekday_first_start
            and agency.weekday_first_end
            and agency.weekday_first_start <= current_time <= agency.weekday_first_end
        ):
            return True
        if (
            agency.weekday_second_start
            and agency.weekday_second_end
            and agency.weekday_second_start <= current_time <= agency.weekday_second_end
        ):
            return True
        else:
            if serializer:
                return False
            raise ValidationError({"message": "Agency closed at this time on weekday"})

    ###########################
    # CURRENT RESERVATION
    ###########################

    @staticmethod
    def get_reserved_tickets(agency_id, user_id):
        eticket_data = ETicketsHelper.fetch_municipality_api_data(agency_id=agency_id)
        url = eticket_data["url"] + f"mesreservation/{user_id}"
        auth = HTTPBasicAuth(eticket_data["auth_user"], eticket_data["auth_password"])
        response = requests.get(url=url, auth=auth).json()
        if response.get("error"):
            response = {"tickets": []}
        return response

    ###########################
    # AGENCY INFO
    ###########################

    @staticmethod
    def get_agency_detail(agency_id):
        eticket_data = ETicketsHelper.fetch_municipality_api_data(agency_id=agency_id)
        url = eticket_data["url"] + f"agence/{eticket_data.get('num_agency')}"
        auth = HTTPBasicAuth(eticket_data["auth_user"], eticket_data["auth_password"])
        return requests.get(url=url, auth=auth).json()

    ###########################
    # ETICKET PDF
    ###########################

    @staticmethod
    def generate_pdf(ticket, agency_id):
        template_name = "eticket.html"

        # Generate QR
        qr_code_data = ticket["qrcode"]
        factory = qrcode.image.svg.SvgImage
        img = qrcode.make(str(qr_code_data), image_factory=factory, box_size=20)
        stream = BytesIO()
        img.save(stream)
        qr_code = stream.getvalue().decode()

        # Prepare the context
        context = {
            "agency": Agency.objects.get(pk=agency_id),
            "date_print": ticket["date_print"],
            "time_print": ticket["heure_print"],
            "service_name": ticket["service"],
            "ticket_number": ticket["num_ticket"],
            "qr_code": qr_code,
        }

        # Generate PDF file
        template = get_template(template_name)
        html = template.render(context)
        pdf = pdfkit.from_string(html, False)

        return pdf
