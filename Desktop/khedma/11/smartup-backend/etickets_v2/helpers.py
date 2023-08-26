from datetime import datetime
from io import BytesIO
from typing import List, Optional, Tuple

import pdfkit
import qrcode
import requests
from django.template.loader import get_template
from haversine import haversine
from pytz import timezone
from rest_framework.exceptions import ValidationError

from backend.enum import TransporationMethods
from backend.models import Reservation
from etickets_v2.models import Agency
from settings.settings import ETICKET_SIGNATURE_SEGMENT_LENGTH


def get_filename():
    time = datetime.today()
    today = time.strftime("%d_%m_%Y")
    return f"eticket_{today}.pdf"


def get_service_prefix(agency):
    arabic_letters = [
        "ا",
        "ب",
        "ج",
        "د",
        "ه",
        "و",
        "ز",
        "ح",
        "ط",
        "ي",
        "ك",
        "ل",
        "م",
        "ن",
        "س",
        "ع",
        "ف",
        "ص",
        "ق",
        "ر",
        "ش",
        "ت",
        "ث",
        "خ",
        "ذ",
        "ض",
        "ظ",
        "غ",
    ]

    prefix_idx = 0
    prefix = arabic_letters[prefix_idx]
    while agency.is_prefix_used(prefix):
        prefix_idx += 1
        prefix = arabic_letters[prefix_idx]
    return prefix


def are_none(elements):
    return all(i is None for i in elements)


def generate_qr(slug: str):
    """
    Args:
        slug (str): the content written in the QR code

    Returns:
        str: stringified stream of a QR code
    """
    factory = qrcode.image.svg.SvgImage
    img = qrcode.make(str(slug), image_factory=factory, box_size=20)
    stream = BytesIO()
    img.save(stream)
    return stream.getvalue().decode()


__to_base_10 = lambda hex_value: int(hex_value, base=16)


def _keep_hex_symbols(input: str) -> str:
    """
    HEX symbols : [0-9] [A-F] [a-f]
    """
    hex_symbols = [str(i) for i in range(10)] + ["a", "b", "c", "d", "e", "f"]
    hex_number = ""
    for c in input.lower():
        if c in hex_symbols:
            hex_number += c
    return hex_number


def _split_signature_segment_to_blocks(string: str, every=3) -> List[str]:
    """
    example string = '12345678907'

    Returns ['123', '456', '789', '07']
    """
    return [string[i : i + every] for i in range(0, len(string), every)]


def decrypt_signature(signature: str) -> List[int]:
    return [
        __to_base_10(_keep_hex_symbols(value))
        for value in _split_signature_segment_to_blocks(
            signature, every=ETICKET_SIGNATURE_SEGMENT_LENGTH
        )
    ]


def generate_pdf(reservation):
    """
    Args:
        reservation (Reservation json)
    Returns:
        pdf
    """
    # Prepare the context
    context = {
        "agency_name": reservation["agency_name"],
        "created_at": reservation["created_at"][0:10],
        "created_at_time": reservation["created_at"][11:19],
        "service_name": reservation["service_name"],
        "ticket_num": reservation["ticket_num"],
        "qr_code": generate_qr(reservation["id"]),
    }

    # Generate PDF file
    template = get_template("reservation.html")
    html = template.render(context)
    pdf = pdfkit.from_string(html, False)
    return pdf


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
            and agency.saturday_first_start <= current_time <= agency.saturday_first_end
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
            raise ValidationError({"message": "Agency closed at this time on saturday"})

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


# Eticket Scoring Helpers
def distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """Calculate the distance in kilometers between two points"""
    return haversine(point1, point2)


def travel_time(
    citizen_lat: float,
    citizen_long: float,
    agency_lat: float,
    agency_long: float,
    time_per_km: float,
) -> float:
    # Calculate the distance between the citizen's location and the agency
    distance_km = distance((citizen_lat, citizen_long), (agency_lat, agency_long))
    travel_time_minutes = distance_km * time_per_km  # max(distance_km , time_per_km)

    return travel_time_minutes


def wait_time(num_people: int, avg_time_per_person: float) -> float:
    """Calculate the total wait time in minutes for an Agency"""
    return num_people * avg_time_per_person


def closest_agency(
    citizen_lat: float,
    citizen_long: float,
    agencies: List[Agency],
    transportation_method: TransporationMethods,
) -> Optional[Agency]:
    """Determine the closest agency to a given location based on the distance, wait time, and transportation method"""
    closest_agency = None
    shortest_time = float("inf")

    for agency in agencies:
        num_people = 0
        for service in agency.services.all():
            num_people += service.get_people_waiting()
        avg_time_per_person = agency.services.first().avg_time_per_person
        travel_time_minutes = travel_time(
            citizen_lat,
            citizen_long,
            agency.latitude,
            agency.longitude,
            transportation_method.value,
        )
        wait_time_minutes = wait_time(num_people, avg_time_per_person)
        # Calculate the total time to reach this agency
        total_time = travel_time_minutes + wait_time_minutes

        # If this is the shortest total time so far, update the closest agency and shortest time
        if total_time < shortest_time:
            closest_agency = agency
            shortest_time = total_time

    return closest_agency
