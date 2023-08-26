from datetime import date
from unittest.mock import patch

import requests
from django.urls import reverse
from freezegun import freeze_time
from httmock import response as mocked_response
from httmock import urlmatch
from model_bakery import baker
from rest_framework import status

from backend.tests.test_base import (
    authenticate_citizen_test,
    authenticate_manager_test,
    ElBaladiyaAPITest,
)
from etickets_v2.models import Agency

LOCAL_SERVER_IP = "196.555.555.155"


@urlmatch(netloc=LOCAL_SERVER_IP)
def mock_local_server(*args):
    headers = {"content-type": "application/json"}
    content = {
        "id": "1d9a6008-285c-4bda-a001-cb368f4e29a6",
        "name": "some_service",
        "description": "",
        "is_active": "true",
        "last_booked_ticket": 100,
        "people_waiting": 80,
        "current_ticket": 20,
        "created_at": "2022-08-22T14:21:36.428886Z",
        "updated_at": "2022-09-17T23:30:35.865082Z",
    }
    return mocked_response(201, content, headers)


class AgenciesTest(ElBaladiyaAPITest):
    def setUp(self):
        super().setUp()
        self.agency = baker.make(
            "etickets_v2.Agency",
            municipality=self.municipality,
            local_ip=LOCAL_SERVER_IP,
        )

    def test_get_agencies(self):  # GET [all]
        agencies = baker.make(
            "etickets_v2.Agency", municipality=self.municipality, _quantity=5
        )
        response = self.client.get(
            reverse("backend:etickets_v2:agencies", args=[self.municipality.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["local_ip"], Agency.objects.all()[0].local_ip)
        self.assertEqual(
            len(response.data), agencies.__len__() + 1
        )  # +1 since we created one in : setUp

    @authenticate_manager_test
    def test_create_agency(self):  # POST {new}
        data = {
            "id": "01d9671a-d574-4936-8fb7-68b2d18bf2ce",
            "is_open": "false",
            "has_eticket": "true",
            "name": "gremda",
            "local_ip": "196.244.158.55",
            "is_active": "false",
            "weekday_first_start": "06:00:00",
            "weekday_first_end": "12:00:00",
            "weekday_second_start": "14:00:00",
            "weekday_second_end": "18:00:00",
            "created_at": "2022-08-06T16:10:01.358457Z",
            "updated_at": "2022-08-06T16:10:01.358475Z",
            "municipality": 1,
            "created_by": "null",
        }
        response = self.client.post(
            reverse("backend:etickets_v2:agencies", args=[self.municipality.pk]),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_service(self):  # GET /id
        response = self.client.get(
            reverse(
                "backend:etickets_v2:agencie",
                args=[self.municipality.pk, self.agency.pk],
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @authenticate_manager_test
    def test_update_agency(self):  # PUT /id
        text = "other"
        data = {"name": text}
        response = self.client.put(
            reverse(
                "backend:etickets_v2:agencie",
                args=[self.municipality.pk, self.agency.pk],
            ),
            data,
            format="json",
        )

        self.assertNotEqual(self.agency.name, text)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.agency.refresh_from_db()
        self.assertEqual(self.agency.name, text)

    @authenticate_manager_test
    def test_delete_agency(self):  # DELETE /id
        response = self.client.delete(
            reverse(
                "backend:etickets_v2:agencie",
                args=[self.municipality.pk, self.agency.pk],
            )
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Agency.objects.filter(pk=self.agency.pk).exists())

    def test_create_agency_unauthorized(self):  # ONLY MANAGER
        data = {
            "name": "string",
        }
        response = self.client.post(
            reverse("backend:etickets_v2:agencies", args=[self.municipality.pk]),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate_citizen_test
    def test_list_reservation(self):  # in all agencies of a municipality
        baker.make(
            "etickets_v2.Reservation",
            created_by=self.citizen.user,
            service__agency__municipality=self.municipality,
            ticket_num=25,
        )
        baker.make(
            "etickets_v2.Reservation",
            created_by=self.citizen.user,
            service__agency__municipality=self.municipality,
            ticket_num=26,
        )

        response = self.client.get(
            reverse(
                "backend:etickets_v2:agencie-all_agencies_reservations",
                args=[self.municipality.pk],
            )
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertTrue(
            response.data[0]["service_name"] != response.data[1]["service_name"]
        )
        self.assertEqual(
            response.data[1]["people_waiting"] - response.data[0]["people_waiting"], 1
        )

        self.assertEqual(
            response.data[0]["total_people_waiting"],
            response.data[1]["total_people_waiting"],
        )
        self.assertTrue(  # both values are int
            isinstance(response.data[0]["total_people_waiting"], int)
            and isinstance(response.data[0]["people_waiting"], int)
        )
        self.assertTrue(  # both values are postive
            response.data[0]["total_people_waiting"] >= 0
            and response.data[0]["people_waiting"] >= 0
        )

    @authenticate_citizen_test
    def test_list_reservation_with_waiting_people(self):
        baker.make(
            "etickets_v2.Reservation",
            created_by=self.citizen.user,
            ticket_num=11,
            service=baker.make(
                "etickets_v2.Service",
                agency__municipality=self.municipality,
                current_ticket=10,
            ),
        )
        baker.make(
            "etickets_v2.Reservation",
            created_by=self.citizen.user,
            ticket_num=10,
            service=baker.make(
                "etickets_v2.Service",
                agency__municipality=self.municipality,
                current_ticket=10,
            ),
        )

        response = self.client.get(
            reverse(
                "backend:etickets_v2:agencie-all_agencies_reservations",
                args=[self.municipality.pk],
            )
        )
        keys = {
            "id",
            "is_still_valid",
            "people_waiting",
            "total_people_waiting",
            "last_booked_ticket",
            "service_name",
            "agency_name",
            "ticket_num",
            "created_at",
            "updated_at",
            "is_active",
            "service",
            "created_by",
            "is_physical",
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["created_by"], self.citizen.user.pk)
        self.assertEqual(response.data[1]["created_by"], self.citizen.user.pk)
        self.assertTrue(response.data[0]["is_active"])
        self.assertTrue(response.data[1]["is_active"])
        self.assertTrue(
            response.data[0]["service_name"] != response.data[1]["service_name"]
        )
        self.assertEqual(keys, set(response.data[0].keys()))
        self.assertEqual(keys, set(response.data[1].keys()))

    @authenticate_citizen_test
    def test_list_reservation_in_agency(self):  # in a single agency
        ticket_number = 9
        baker.make(
            "etickets_v2.Reservation",
            created_by=self.citizen.user,
            service__agency=self.agency,
            service__current_ticket=ticket_number,
            ticket_num=ticket_number,
        )
        baker.make(
            "etickets_v2.Reservation",
            created_by=self.citizen.user,
            service__agency__municipality=self.agency.municipality,
            service__current_ticket=ticket_number,
            ticket_num=ticket_number,
        )

        response = self.client.get(
            reverse(
                "backend:etickets_v2:reservationss",
                args=[self.municipality.pk, self.agency.pk],
            )
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    @authenticate_citizen_test
    def test_get_reservation_pdf_by_id(self):
        ticket_number = 9
        reservation = baker.make(
            "etickets_v2.Reservation",
            created_by=self.citizen.user,
            service__agency=self.agency,
            service__current_ticket=ticket_number,
            ticket_num=ticket_number,
            is_active=True,
        )
        response = self.client.get(
            reverse(
                "backend:etickets_v2:reservations-pdf_reservation",
                args=[self.municipality.pk, self.agency.pk, reservation.pk],
            )
        )

        file_name = f'"eticket_{date.today().strftime("%d_%m_%Y")}.pdf"'
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.get("Content-Disposition"), "attachment; filename=" + file_name
        )

    @authenticate_citizen_test
    @freeze_time("2021-01-12")
    def test_get_no_longer_valid_reservations_by_id(self):
        ticket_number = 9
        reservation = baker.make(
            "etickets_v2.Reservation",
            service__agency=self.agency,
            service__current_ticket=ticket_number,
            ticket_num=ticket_number - 1,
        )

        response = self.client.get(
            reverse(
                "backend:etickets_v2:reservations-pdf_reservation",
                args=[self.municipality.pk, self.agency.pk, reservation.pk],
            )
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @freeze_time("2021-01-12")
    @authenticate_citizen_test
    def test_get_no_longer_valid_reservations_in_agency(self):
        baker.make(
            "etickets_v2.Reservation",
            service__agency=self.agency,
            service__current_ticket=10,
            ticket_num=9,
            created_by=self.citizen.user,
        )

        response = self.client.get(
            reverse(
                "backend:etickets_v2:reservationss",
                args=[self.municipality.pk, self.agency.pk],
            )
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
        response = self.client.get(
            reverse(
                "backend:etickets_v2:agencie-all_agencies_reservations",
                args=[self.municipality.pk],
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    @authenticate_citizen_test
    def test_verify_reservation_true(self):
        reservation = baker.make("etickets_v2.Reservation", service__agency=self.agency)

        response = self.client.get(
            reverse(
                "backend:etickets_v2:reservations-verify_reservation",
                args=[
                    self.municipality.pk,
                    self.agency.pk,
                    f"{reservation.pk}",
                ],
            )
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data)

    @authenticate_citizen_test
    def test_verify_reservation_false(self):
        agency2 = baker.make(
            "etickets_v2.Agency", municipality=self.municipality, name="string2"
        )
        reservation = baker.make("etickets_v2.Reservation", service__agency=self.agency)

        response = self.client.get(
            reverse(
                "backend:etickets_v2:reservations-verify_reservation",
                args=[
                    self.municipality.pk,
                    agency2.pk,
                    f"{reservation.pk}5151",
                ],
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data)

    @patch("requests.post")
    @authenticate_citizen_test
    def test_cancel_reservation(self, mocked_response):
        def res():
            response = requests.Response()
            response.status_code = status.HTTP_200_OK

            def json_func():
                return {}

            response.json = json_func
            return response

        mocked_response.return_value = res()
        reservation = baker.make(
            "etickets_v2.Reservation",
            ticket_num=100,
            created_by=self.citizen.user,
            service__agency=self.agency,
        )
        response = self.client.post(
            reverse(
                "backend:etickets_v2:reservations-cancel_reservation",
                args=[self.municipality.pk, self.agency.pk, reservation.pk],
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_active"])

        response = self.client.get(
            reverse(
                "backend:etickets_v2:agencie-all_agencies_reservations",
                args=[self.municipality.pk],
            )
        )
        self.assertTrue(len(response.data) == 0)

    @patch("requests.post")
    @authenticate_citizen_test
    def test_cancel_reservation_not_found(self, mocked_response):
        incorrect_ticket_num = 9999
        response = self.client.post(
            reverse(
                "backend:etickets_v2:reservations-cancel_reservation",
                args=[self.municipality.pk, self.agency.pk, incorrect_ticket_num],
            )
        )

        self.assertNotFoundResponse(response, should_have_details=False)

    @authenticate_citizen_test
    @patch("requests.post")
    def test_cancel_reservation_with_local_called(self, mock_post):
        mock_post.return_value.status_code = 200
        self.agency.secured_connection = True
        self.agency.save()
        reservation = baker.make(
            "etickets_v2.Reservation",
            ticket_num=100,
            created_by=self.citizen.user,
            service__agency=self.agency,
        )
        response = self.client.post(
            reverse(
                "backend:etickets_v2:reservations-cancel_reservation",
                args=[self.municipality.pk, self.agency.pk, reservation.pk],
            )
        )
        headers = {"Content-type": "application/json"}
        url = f"https://{self.agency.local_ip}/api/services/{reservation.service.id}/cancel-ticket/"
        data = {"ticket_num": 100}
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_post.assert_called_with(url, json=data, headers=headers)

    @authenticate_citizen_test
    @patch("requests.post")
    def test_cancel_reservation_with_local_not_called(self, mock_post):
        mock_post.return_value.status_code = 500
        reservation = baker.make(
            "etickets_v2.Reservation",
            ticket_num=100,
            created_by=self.citizen.user,
            service__agency=self.agency,
        )
        response = self.client.post(
            reverse(
                "backend:etickets_v2:reservations-cancel_reservation",
                args=[self.municipality.pk, self.agency.pk, reservation.pk],
            )
        )
        headers = {"Content-type": "application/json"}
        url = f"http://{self.agency.local_ip}/api/services/{reservation.service.id}/cancel-ticket/"
        data = {"ticket_num": 100}
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        mock_post.assert_called_with(url, json=data, headers=headers)

    @patch("requests.post")
    @authenticate_citizen_test
    def test_cancel_reservation_aready_passed(self, mocked_response):
        def res():
            response = requests.Response()
            response.status_code = status.HTTP_200_OK

            def json_func():
                return {}

            response.json = json_func
            return response

        mocked_response.return_value = res()

        reservation = baker.make(
            "etickets_v2.Reservation",
            ticket_num=10,
            created_by=self.citizen.user,
            service=baker.make(
                "etickets_v2.Service", current_ticket=10, agency=self.agency
            ),
        )
        response = self.client.post(
            reverse(
                "backend:etickets_v2:reservations-cancel_reservation",
                args=[self.municipality.pk, self.agency.pk, reservation.pk],
            )
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_all_agencies(self):
        baker.make(
            "etickets_v2.Agency",
            _quantity=10,
        )
        response = self.client.get(
            reverse(
                "backend:get-all-agencies",
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 11)  # one created in setup

    def test_get_all_agencies_with_all_details(self):
        baker.make(
            "etickets_v2.Agency",
            _quantity=10,
        )
        response = self.client.get(
            reverse(
                "backend:get-all-agencies",
            )
        )
        keys = [
            "id",
            "is_open",
            "has_eticket",
            "municipality_name",
            "name",
            "is_active",
            "latitude",
            "longitude",
            "weekday_first_start",
            "weekday_first_end",
            "weekday_second_start",
            "weekday_second_end",
            "saturday_first_start",
            "saturday_first_end",
            "saturday_second_start",
            "saturday_second_end",
            "created_at",
            "updated_at",
            "municipality",
            "created_by",
        ]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for key in keys:
            self.assertTrue(key in response.data[0].keys())

    @authenticate_citizen_test
    def test_people_waiting_for_reservation(self):
        service = baker.make(
            "etickets_v2.Service",
            current_ticket=25,
            last_booked_ticket=60,
            agency=self.agency,
        )
        baker.make(
            "etickets_v2.Reservation",
            ticket_num=30,
            service=service,
            created_by=self.citizen.user,
        )
        response = self.client.get(
            reverse(
                "backend:etickets_v2:reservationss",
                args=[self.municipality.pk, self.agency.pk],
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["people_waiting"], 5)  # 30 - 25
        self.assertEqual(response.data[0]["total_people_waiting"], 35)  # 60 - 25

    @authenticate_citizen_test
    @freeze_time("22-01-12")
    def test_can_get_reservation_when_is_being_called(self):
        """citizen should be able to retrieve his reservation as long as it didn't pass yet"""
        service = baker.make(
            "etickets_v2.Service",
            agency=self.agency,
            current_ticket=9,
            last_booked_ticket=20,
        )

        reservation = baker.make(
            "etickets_v2.Reservation",
            created_by=self.citizen.user,
            service=service,
            ticket_num=9,
            is_active=True,
        )
        response = self.client.get(
            reverse(
                "backend:etickets_v2:reservationss",
                args=[self.municipality.pk, self.agency.pk],
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(
            reverse(
                "backend:etickets_v2:agencie-all_agencies_reservations",
                args=[self.municipality.pk],
            )
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(
            reverse(
                "backend:etickets_v2:reservations-pdf_reservation",
                args=[self.municipality.pk, self.agency.pk, reservation.pk],
            )
        )

        file_name = f'"eticket_{date.today().strftime("%d_%m_%Y")}.pdf"'
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.get("Content-Disposition"), "attachment; filename=" + file_name
        )

    @authenticate_citizen_test
    @freeze_time("22-01-12")
    def test_no_way_to_retrieve_reservation_after_it_passes(self):
        """citizen should not be able to retrieve his reservation if passed"""
        service = baker.make(
            "etickets_v2.Service",
            agency=self.agency,
            current_ticket=9,
            last_booked_ticket=20,
        )
        reservation = baker.make(
            "etickets_v2.Reservation",
            created_by=self.citizen.user,
            service=service,
            ticket_num=8,
            is_active=True,
        )
        response = self.client.get(
            reverse(
                "backend:etickets_v2:reservationss",
                args=[self.municipality.pk, self.agency.pk],
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        response = self.client.get(
            reverse(
                "backend:etickets_v2:agencie-all_agencies_reservations",
                args=[self.municipality.pk],
            )
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        response = self.client.get(
            reverse(
                "backend:etickets_v2:reservations-pdf_reservation",
                args=[self.municipality.pk, self.agency.pk, reservation.pk],
            )
        )
        # citizen can't get it even by id since it's it passed
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
