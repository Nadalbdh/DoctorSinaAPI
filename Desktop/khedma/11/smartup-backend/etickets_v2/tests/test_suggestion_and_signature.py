from random import choice

from django.urls import reverse
from freezegun import freeze_time
from model_bakery import baker
from rest_framework import status

from backend.tests.test_base import authenticate_citizen_test, ElBaladiyaAPITest
from etickets_v2.helpers import (
    _keep_hex_symbols,
    _split_signature_segment_to_blocks,
    decrypt_signature,
)
from etickets_v2.models import Reservation
from settings.settings import ETICKET_SIGNATURE_SEGMENT_LENGTH


class TestClosestAgency(ElBaladiyaAPITest):
    @authenticate_citizen_test
    def test_closest_agency_driving_near(self):
        # Test with a citizen located close to the agencies
        citizen_lat = 36.80
        citizen_long = 10.18
        data = {
            "latitude": citizen_lat,
            "longitude": citizen_long,
            "transporation_method": "WALKING",
        }

        agency1 = baker.make(
            "etickets_v2.Agency",
            municipality=self.municipality,
            name="Agency 1",
            latitude=citizen_lat,
            longitude=citizen_long,
        )
        agency2 = baker.make(
            "etickets_v2.Agency",
            municipality=self.municipality,
            name="Agency 2",
            latitude=citizen_lat,
            longitude=citizen_long + 0.5,
        )
        baker.make(
            "etickets_v2.Service",
            last_booked_ticket=50,
            current_ticket=1,
            created_by=self.citizen.user,
            agency=agency1,
            _quantity=3,  # waiting people = 49*3
        )
        baker.make(
            "etickets_v2.Service",
            last_booked_ticket=5,
            current_ticket=1,
            created_by=self.citizen.user,
            agency=agency2,
            _quantity=3,  # waiting people = 4*3
        )
        response = self.client.post(
            reverse(
                "backend:etickets_v2:eticket-scoring",
                args=[self.municipality.pk],
            ),
            data,
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Agency 2")

    @authenticate_citizen_test
    def test_use_transporation_method_notfound_should_return_400(self):
        data = {
            "latitude": 11.2,
            "longitude": 10.0,
            "transporation_method": "NOTFOUND",
        }
        response = self.client.post(
            reverse(
                "backend:etickets_v2:eticket-scoring",
                args=[self.municipality.pk],
            ),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @authenticate_citizen_test
    def test_decrypt_signature(self):
        cases = [
            [12, 56],
            [85, 88],
            [78, 13],
            [100, 99],
            [77, 1],
            [778, 2],
            [12, 445],
            [858, 934],
            [2, 934],
        ]
        for expected in cases:
            fake_signature = self.fake_signature_from(expected[0], expected[1])
            actual = decrypt_signature(fake_signature)
            self.assertEqual(expected, actual)

    def test_decrypt_signature_functions(self):
        expected = "abcdef123456789"
        actual = _keep_hex_symbols("ABCdefghijklMnoPQrstuvwxyz123456789#%")
        self.assertEqual(expected, actual)

        expected = ["123", "456", "789", "07"]
        actual = _split_signature_segment_to_blocks("12345678907")
        self.assertEqual(expected, actual)

    def fake_signature_from(self, service_id: int, ticket_number: int):
        """mimic how the local server would generate a signature"""
        return f"{self.fake_encrypt(service_id)}{self.fake_encrypt(ticket_number)}"

    def fake_encrypt(self, input: int):
        hex_value = f"{input:x}"
        while len(hex_value) < ETICKET_SIGNATURE_SEGMENT_LENGTH:
            random_filler = choice(
                [
                    "g",
                    "h",
                    "i",
                    "j",
                    "k",
                    "l",
                    "m",
                    "n",
                    "o",
                    "p",
                    "q",
                    "r",
                    "s",
                    "t",
                    "u",
                    "v",
                    "w",
                    "x",
                    "y",
                    "z",
                ]
            )
            hex_value = hex_value + random_filler
        return hex_value

    @authenticate_citizen_test
    @freeze_time("2021-01-12")
    def test_convert_physical_ticket_with_invalid_signature(self):
        service = baker.make(
            "etickets_v2.Service",
            current_ticket=10,
            last_booked_ticket=20,
            created_by=self.citizen.user,
        )
        response = self.client.post(
            reverse(
                "backend:etickets_v2:convert-physical-ticket",
                args=[self.municipality.pk],
            ),
            {
                "signature": self.fake_signature_from(service.id, 10),
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.post(
            reverse(
                "backend:etickets_v2:convert-physical-ticket",
                args=[self.municipality.pk],
            ),
            {
                "signature": self.fake_signature_from(service.id, 21),
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate_citizen_test
    @freeze_time("2021-01-12")
    def test_convert_physical_ticket_with_signature(self):
        service = baker.make(
            "etickets_v2.Service",
            current_ticket=10,
            last_booked_ticket=20,
        )
        data = {
            "signature": self.fake_signature_from(service.id, 15),
        }
        response = self.client.post(
            reverse(
                "backend:etickets_v2:convert-physical-ticket",
                args=[self.municipality.pk],
            ),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["created_by"], self.citizen.user.pk)
        self.assertEqual(Reservation.objects.count(), 1)
        self.assertEqual(Reservation.objects.first().ticket_num, 15)
        self.assertEqual(Reservation.objects.first().is_physical, True)
        self.assertEqual(Reservation.objects.first().service.id, service.id)
