from unittest import mock
from unittest.mock import patch

from django.urls import reverse
from freezegun import freeze_time
from rest_framework import status

from backend.tests.test_base import authenticate_citizen_test, ElBaladiyaAPITest


class ETicketsTest(ElBaladiyaAPITest):
    def setUp(self):
        super().setUp()
        self.agency = self.make_with_municipality(
            model="etickets.agency",
            is_active=True,
        )

    @authenticate_citizen_test
    @patch("etickets.helper_functions.ETicketsHelper.process_api_reservation")
    @freeze_time("2021-09-01")
    def test_reservation_success(self, mock_post):
        my_mock_response = mock.Mock(status_code=200)
        my_mock_response.json.return_value = {
            "error": False,
            "message": "succés",
            "infoticket": {
                "ticket": {
                    "numeroticket": "602",
                    "nbattente": "01",
                    "date": "2021-09-01",
                    "heure": "00:00:00",
                    "service": "خدمات 3",
                    "prefix": "C",
                    "agence": "Express_Display",
                },
                "reponse": "ok",
            },
        }
        mock_post.return_value = my_mock_response
        data = {"service_id": 3}
        resp = self.client.post(
            reverse("etickets:reservations", args=[self.agency.pk]), data, format="json"
        )
        expected_output = {
            "id": 1,
            "ticket_info_json": {
                "numeroticket": "602",
                "nbattente": "01",
                "date": "2021-09-01",
                "heure": "00:00:00",
                "service": "خدمات 3",
                "prefix": "C",
                "agence": "Express_Display",
            },
            "service_name": "خدمات 3",
            "service_id": 3,
            "ticket_num": 602,
            "is_active": True,
            "created_at": "2021-09-01T00:00:00Z",
            "agency": self.agency.pk,
            "created_by": self.citizen.user.pk,
        }
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertDictEqual(resp.data, expected_output)

    @authenticate_citizen_test
    @patch("etickets.helper_functions.ETicketsHelper.process_api_reservation")
    @freeze_time("2021-09-01")
    def test_reservation_error(self, mock_post):
        my_mock_response = mock.Mock(status_code=201)
        my_mock_response.json.return_value = {
            "error": "You have already reserved for this service, try again later"
        }
        mock_post.return_value = my_mock_response
        data = {"service_id": 3}
        resp = self.client.post(
            reverse("etickets:reservations", args=[self.agency.pk]), data, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    @authenticate_citizen_test
    @patch("etickets.helper_functions.ETicketsHelper.get_reserved_tickets")
    def test_get_current_reservation(self, mock_get):
        mock_get.return_value = {
            "tickets": [
                {
                    "num_ticket": "602",
                    "date_print": "2021-09-11",
                    "heure_print": "18:57:29",
                    "called": 0,
                    "qrcode": "",
                    "jour_semaine": 6,
                    "service": "خدمات 3",
                    "prefixe": "C",
                    "id_client": "2",
                    "id_agence": "1921681111",
                    "nom_agence": "Express_Display",
                    "num_guichet": 0,
                    "id_service": 3,
                    "idcompte": 4,
                    "nbattente": "01",
                }
            ]
        }
        resp = self.client.get(
            reverse("etickets:current_reservation", args=[self.agency.pk]),
            format="json",
        )
        expected_output = {
            "tickets": [
                {
                    "num_ticket": "602",
                    "date_print": "2021-09-11",
                    "heure_print": "18:57:29",
                    "called": 0,
                    "qrcode": "",
                    "jour_semaine": 6,
                    "service": "خدمات 3",
                    "prefixe": "C",
                    "id_client": "2",
                    "id_agence": "1921681111",
                    "nom_agence": "Express_Display",
                    "num_guichet": 0,
                    "id_service": 3,
                    "idcompte": 4,
                    "nbattente": "01",
                }
            ]
        }
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertDictEqual(resp.data, expected_output)

    @authenticate_citizen_test
    @freeze_time("2021-09-01")
    @patch("etickets.helper_functions.ETicketsHelper.get_reserved_tickets")
    def test_download_eticket_pdf(self, mock_get):
        id_service = 3
        mock_get.return_value = {
            "tickets": [
                {
                    "num_ticket": "602",
                    "date_print": "2021-09-11",
                    "heure_print": "18:57:29",
                    "called": 0,
                    "qrcode": "",
                    "jour_semaine": 6,
                    "service": "خدمات 3",
                    "prefixe": "C",
                    "id_client": "2",
                    "id_agence": "1921681111",
                    "nom_agence": "Express_Display",
                    "num_guichet": 0,
                    "id_service": 3,
                    "idcompte": 4,
                    "nbattente": "01",
                }
            ]
        }
        resp = self.client.get(
            reverse("etickets:my_eticket", args=[self.agency.pk, id_service]),
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(
            resp.get("Content-Disposition"),
            'attachment; filename="eticket_01_09_2021.pdf"',
        )

    @authenticate_citizen_test
    @patch("etickets.helper_functions.ETicketsHelper.get_agency_detail")
    def test_get_agency_details(self, mock_get):
        eticket_id = 1
        mock_get.return_value = {
            "agence": {
                "id": 2,
                "horaire_ouverture": "8:30h",
                "heure_fermeture": "19h",
                "nom_agence": "Express_Display",
                "chef": "Responsable",
                "governerat": "Tunis",
                "lieu": "Ariana",
                "logo": "logo.png",
                "gps_x": "36.85312",
                "gps_y": "10.18950",
                "adresse_ip": "127.0.0.1",
                "ip_server": "127.0.0.1",
                "num_agence": "1921681111",
                "email": None,
                "tel": None,
                "fax": None,
                "statut": 1,
                "nbattente": "04",
                "encombrement": 1,
                "services": [
                    {
                        "id": 1,
                        "nom_service": "خدمات 1",
                        "prefixe": "A",
                        "nom_service_ar": "خدمات 1",
                        "nom_service_en": "خدمات 1",
                        "nbattente": "01",
                        "lastnum": "01",
                        "lasttrait": "",
                    },
                    {
                        "id": 2,
                        "nom_service": "خدمات 2",
                        "prefixe": "B",
                        "nom_service_ar": "خدمات 2",
                        "nom_service_en": "خدمات 2",
                        "nbattente": "02",
                        "lastnum": "302",
                        "lasttrait": "",
                    },
                    {
                        "id": 3,
                        "nom_service": "خدمات 3",
                        "prefixe": "C",
                        "nom_service_ar": "خدمات 3",
                        "nom_service_en": "خدمات 3",
                        "nbattente": "01",
                        "lastnum": "601",
                        "lasttrait": "",
                    },
                ],
            }
        }
        resp = self.client.get(
            reverse("etickets:agency", args=[eticket_id]), format="json"
        )
        expected_output = {
            "id": 1,
            "status": resp.data.get("status"),
            "name": self.agency.name,
            "is_active": True,
            "weekday_first_start": str(self.agency.weekday_first_start),
            "weekday_first_end": str(self.agency.weekday_first_end),
            "weekday_second_start": str(self.agency.weekday_second_start),
            "weekday_second_end": str(self.agency.weekday_second_end),
            "saturday_first_start": None,
            "saturday_first_end": None,
            "saturday_second_start": None,
            "saturday_second_end": None,
            "municipality": self.municipality.pk,
            "agence": {
                "id": 2,
                "horaire_ouverture": "8:30h",
                "heure_fermeture": "19h",
                "nom_agence": "Express_Display",
                "chef": "Responsable",
                "governerat": "Tunis",
                "lieu": "Ariana",
                "logo": "logo.png",
                "gps_x": "36.85312",
                "gps_y": "10.18950",
                "adresse_ip": "127.0.0.1",
                "ip_server": "127.0.0.1",
                "num_agence": "1921681111",
                "email": None,
                "tel": None,
                "fax": None,
                "statut": 1,
                "nbattente": "04",
                "encombrement": 1,
                "services": [
                    {
                        "id": 1,
                        "nom_service": "خدمات 1",
                        "prefixe": "A",
                        "nom_service_ar": "خدمات 1",
                        "nom_service_en": "خدمات 1",
                        "nbattente": "01",
                        "lastnum": "01",
                        "lasttrait": "",
                    },
                    {
                        "id": 2,
                        "nom_service": "خدمات 2",
                        "prefixe": "B",
                        "nom_service_ar": "خدمات 2",
                        "nom_service_en": "خدمات 2",
                        "nbattente": "02",
                        "lastnum": "302",
                        "lasttrait": "",
                    },
                    {
                        "id": 3,
                        "nom_service": "خدمات 3",
                        "prefixe": "C",
                        "nom_service_ar": "خدمات 3",
                        "nom_service_en": "خدمات 3",
                        "nbattente": "01",
                        "lastnum": "601",
                        "lasttrait": "",
                    },
                ],
            },
        }
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertDictEqual(resp.data, expected_output)
