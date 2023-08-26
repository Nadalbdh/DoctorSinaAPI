from django.core.exceptions import ValidationError
from django.test import override_settings
from django.urls import reverse
from freezegun import freeze_time
from guardian.shortcuts import assign_perm
from httmock import HTTMock
from httmock import response as mocked_response
from httmock import urlmatch
from model_bakery import baker
from rest_framework import status
from rest_framework_api_key.models import APIKey

from backend.enum import MunicipalityPermissions
from backend.helpers import ManagerHelpers
from backend.tests.test_base import (
    authenticate_citizen_test,
    authenticate_manager_test,
    ElBaladiyaAPITest,
)
from etickets_v2.models import Reservation, Service
from etickets_v2.serializers import ReservationSerializer, ServiceSerializer
from notifications.models import Notification

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


class ServicesTest(ElBaladiyaAPITest):
    def setUp(self):
        super().setUp()
        self.api_key, self.key = APIKey.objects.create_key(name="remote-service")
        self.agency = baker.make(
            "etickets_v2.Agency",
            municipality=self.municipality,
            local_ip=LOCAL_SERVER_IP,
        )
        self.service = baker.make("etickets_v2.Service", agency=self.agency)
        self.mock_services = [
            ServiceSerializer(self.service).data,
            {
                "id": "3969",
                "people_waiting": 10,
                "name": "خدمة 1",
                "description": "تمكن هذه الخدمة طالبي الشغل المرسمين بمكاتب التشغيل والعمل المستقل من تحيين البيانات الخاصة",
                "is_active": "true",
                "last_booked_ticket": 25,
                "current_ticket": 15,
                "created_at": "2022-08-03T23:27:03.245927Z",
                "updated_at": "2022-08-03T23:27:03.245954Z",
                "created_by": 2,
            },
        ]
        # to test pushing old data is being overridden
        self.mock_services[0]["name"] = "some old name that was changed"

    def test_get_services(self):  # GET [all]
        COUNT = 5
        baker.make("etickets_v2.Service", agency=self.agency, _quantity=COUNT)

        response = self.client.get(
            reverse(
                "backend:etickets_v2:services",
                args=[self.municipality.pk, self.agency.pk],
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data), COUNT + 1
        )  # +1 since we created one in : setUp

    def test_get_all_services_details(self):  # GET [all]
        COUNT = 5
        baker.make("etickets_v2.Service", agency=self.agency, _quantity=COUNT)

        response = self.client.get(
            reverse(
                "backend:etickets_v2:services",
                args=[self.municipality.pk, self.agency.pk],
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), COUNT + 1)
        keys = [
            "id",
            "people_waiting",
            "name",
            "description",
            "is_active",
            "last_booked_ticket",
            "current_ticket",
            "created_at",
            "updated_at",
            "created_by",
            "agency",
            "avg_time_per_person",
        ]
        for service in response.data:
            self.assertEqual(set(keys), set(service.keys()))

    @authenticate_manager_test
    def test_create_service(self):  # POST {new}
        data = {
            "name": "string",
            "description": "string",
            "is_active": "true",
            "last_booked_ticket": 0,
            "current_ticket": 0,
            "created_by": 0,
            "avg_time_per_person": 8,
            "agency": self.agency.id,
        }
        response = self.client.post(
            reverse(
                "backend:etickets_v2:services",
                args=[self.municipality.pk, self.agency.pk],
            ),
            data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_service(self):  # GET /id
        response = self.client.get(
            reverse(
                "backend:etickets_v2:service",
                args=[self.municipality.pk, self.agency.pk, self.service.pk],
            ),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @authenticate_manager_test
    def test_update_service_by_manager(self):  # PUT /id auth manager
        assign_perm(
            MunicipalityPermissions.MANAGE_ETICKET,
            self.manager.user,
            self.municipality,
        )
        ManagerHelpers(self.manager, self.municipality).assign_permissions(
            [MunicipalityPermissions.MANAGE_ETICKET]
        )
        text = "other"
        data = {"description": text}
        response = self.client.put(
            reverse(
                "backend:etickets_v2:service",
                args=[self.municipality.pk, self.agency.pk, self.service.pk],
            ),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(self.service.description, text)
        self.service.refresh_from_db()
        self.assertEqual(self.service.description, text)

    def test_update_service_by_token(self):  # PUT /id auth token
        text = "other"
        data = {"description": text}
        self.assertNotEqual(self.service.description, text)
        response = self.client.put(
            reverse(
                "backend:etickets_v2:service",
                args=[self.municipality.pk, self.agency.pk, self.service.pk],
            ),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.service.refresh_from_db()
        self.assertNotEqual(self.service.description, text)

        response = self.client.put(
            reverse(
                "backend:etickets_v2:service",
                args=[self.municipality.pk, self.agency.pk, self.service.pk],
            ),
            data,
            format="json",
            HTTP_AUTHORIZATION=f"Api-Key {self.key}",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.service.refresh_from_db()
        self.assertEqual(self.service.description, text)

    @authenticate_manager_test
    def test_delete_service(self):  # DELETE /id
        response = self.client.delete(
            reverse(
                "backend:etickets_v2:service",
                args=[self.municipality.pk, self.agency.pk, self.service.pk],
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Service.objects.filter(pk=self.service.pk).exists())

    @authenticate_citizen_test
    def test_create_service_unauthorized_not_manager(self):  # ONLY MANAGER
        data = {
            "name": "string",
            "description": "string",
            "is_active": "true",
            "last_booked_ticket": 0,
            "current_ticket": 0,
            "created_by": 0,
            "agency": self.agency.id,
        }

        response = self.client.post(
            reverse(
                "backend:etickets_v2:services",
                args=[self.municipality.pk, self.agency.pk],
            ),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_push_all_services_with_token(self):  # PATCH [all]
        self.assertEqual(Service.objects.count(), 1)
        self.assertNotEqual(Service.objects.first().name, self.mock_services[0]["name"])
        response = self.client.patch(
            reverse(
                "backend:etickets_v2:service-push_all",
                args=[self.municipality.pk, self.agency.pk],
            ),
            self.mock_services,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Service.objects.count(), 1)

        response = self.client.patch(
            reverse(
                "backend:etickets_v2:service-push_all",
                args=[self.municipality.pk, self.agency.pk],
            ),
            self.mock_services,
            format="json",
            HTTP_AUTHORIZATION=f"Api-Key {self.key}",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Service.objects.first().name, self.mock_services[0]["name"])
        self.assertEqual(
            Service.objects.count(), 1
        )  # should drop the extra services if they don't exist in

    @authenticate_citizen_test
    def test_book_reservation(self):
        with HTTMock(mock_local_server):
            response = self.client.get(
                reverse(
                    "backend:etickets_v2:service-book",
                    args=[self.municipality.pk, self.agency.pk, self.service.pk],
                )
            )
        reservation_in_db = ReservationSerializer(
            Reservation.objects.all().first()
        ).data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], reservation_in_db["id"])
        self.assertEqual(
            response.data["is_still_valid"], reservation_in_db["is_still_valid"]
        )
        self.assertEqual(
            response.data["last_booked_ticket"],
            # 100 is hard coded in the mock
            100,
        )
        self.assertEqual(
            sorted(response.data.keys()),
            sorted(
                [
                    "is_physical",
                    "created_by",
                    "last_booked_ticket",
                    "created_at",
                    "id",
                    "ticket_num",
                    "agency_name",
                    "people_waiting",
                    "service",
                    "updated_at",
                    "is_still_valid",
                    "total_people_waiting",
                    "service_name",
                    "is_active",
                ]
            ),
        )

    @authenticate_citizen_test
    def test_book_reservation_already_booked(self):
        baker.make(
            "etickets_v2.Reservation",
            created_by=self.citizen.user,
            service=self.service,
            ticket_num=self.service.current_ticket,
        )
        with HTTMock(mock_local_server):
            response = self.client.get(
                reverse(
                    "backend:etickets_v2:service-book",
                    args=[self.municipality.pk, self.agency.pk, self.service.pk],
                )
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["message"], "user already has an e-ticket for this service."
        )

    @freeze_time("2021-01-12")
    def test_number_of_waiting_people(self):
        service = baker.make(
            "etickets_v2.Service",
            agency=self.agency,
            current_ticket=2,
            last_booked_ticket=6,
        )
        baker.make(
            "etickets_v2.Reservation",
            service=service,
            ticket_num=1,  # no longer accounted for
            is_active=True,
            created_at="2021-01-12",
        )
        reservation = baker.make(
            "etickets_v2.Reservation",
            service=service,
            ticket_num=2,  # we not consider him as waiting
            is_physical=True,
            is_active=True,
            created_at="2021-01-12",
        )

        baker.make(
            "etickets_v2.Reservation",
            service=service,
            ticket_num=3,
            is_physical=False,
            is_active=True,
            created_at="2021-01-12",
        )
        # number 4 was physical
        baker.make(
            "etickets_v2.Reservation",
            service=service,
            ticket_num=5,
            is_physical=False,
            is_active=True,
            created_at="2021-01-12",
        )
        # number 6 was physical

        response = self.client.get(
            reverse(
                "backend:etickets_v2:service",
                args=[self.municipality.pk, self.agency.pk, service.pk],
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["people_waiting"], 4)
        # Cancel the 2nd ticket
        reservation.is_active = False
        reservation.save()
        response = self.client.get(
            reverse(
                "backend:etickets_v2:service",
                args=[self.municipality.pk, self.agency.pk, service.pk],
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["people_waiting"], 3)

    @authenticate_citizen_test
    @freeze_time("2021-01-12")
    @override_settings(MAX_NB_TICKETS_PER_DAY_FOR_USER=10)
    def test_max_reservations_per_user_per_day(self):
        with freeze_time("2012-01-05"):
            baker.make(
                "etickets_v2.Reservation",
                is_active=False,
                service=self.service,
                created_by=self.citizen.user,
                _quantity=3,
            )
        baker.make(
            "etickets_v2.Reservation",
            service__agency=self.agency,
            created_by=self.citizen.user,
            is_active=False,
            _quantity=9,
        )
        with HTTMock(mock_local_server):
            response = self.client.get(
                reverse(
                    "backend:etickets_v2:service-book",
                    args=[self.municipality.pk, self.agency.pk, self.service.pk],
                )
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Reservation.objects.filter(
                created_by=self.citizen.user, created_at="2021-01-12"
            ).count(),
            10,
        )
        deactivate_last_booked_eticket = Reservation.objects.last()
        deactivate_last_booked_eticket.is_active = False
        deactivate_last_booked_eticket.save(update_fields=["is_active"])

        with HTTMock(mock_local_server):
            response = self.client.get(
                reverse(
                    "backend:etickets_v2:service-book",
                    args=[self.municipality.pk, self.agency.pk, self.service.pk],
                )
            )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(
            Reservation.objects.filter(
                created_by=self.citizen.user, created_at="2021-01-12"
            ).count(),
            10,
        )

    @freeze_time("2021-01-12T07:00")
    def test_service_resetting_every_day(self):
        services = baker.make(
            "etickets_v2.Service",
            current_ticket=5,
            last_booked_ticket=55,
            agency=self.agency,
            _quantity=4,
        )
        services_json = []
        for service in services:
            services_json.append(ServiceSerializer(service).data)
        response = self.client.patch(
            reverse(
                "backend:etickets_v2:service-push_all",
                args=[self.municipality.pk, self.agency.pk],
            ),
            services_json,
            format="json",
            HTTP_AUTHORIZATION=f"Api-Key {self.key}",
        )
        self.assertEqual(response.status_code, 201)
        for service in services:
            service.refresh_from_db()
            self.assertEqual(service.current_ticket, 0)
            self.assertIsNone(service.last_booked_ticket)

    def test_push_notifications(self):
        """assert notifications created for last 5 reservations on a local server PUT"""
        # create 10 citizens with reservations
        NB_SHOULD_RECEIVE_NOTIFS = 5
        for i in range(NB_SHOULD_RECEIVE_NOTIFS):
            baker.make(
                "etickets_v2.Reservation",
                service=self.service,
                ticket_num=self.service.current_ticket + i,
                is_active=True,
            )
        notifications_count = lambda: Notification.objects.count()
        self.assertEqual(notifications_count(), 0)
        response = self.client.post(
            reverse(
                "backend:etickets_v2:service-send_notifications",
                args=[self.municipality.pk, self.agency.pk, self.service.pk],
            ),
            {},
            format="json",
            HTTP_AUTHORIZATION=f"Api-Key {self.key}",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(notifications_count(), NB_SHOULD_RECEIVE_NOTIFS)

    def test_push_notifications_message(self):
        service = baker.make(
            "etickets_v2.Service",
            name="service 1",
            agency=self.agency,
            current_ticket=25,
            last_booked_ticket=50,
        )
        baker.make(
            "etickets_v2.Reservation",
            service=service,
            ticket_num=26,
            is_active=True,
        )
        self.assertEqual(Notification.objects.count(), 0)
        response = self.client.post(
            reverse(
                "backend:etickets_v2:service-send_notifications",
                args=[self.municipality.pk, self.agency.pk, service.pk],
            ),
            {},
            format="json",
            HTTP_AUTHORIZATION=f"Api-Key {self.key}",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(
            Notification.objects.first().body,
            f"يرجى التقدم إلى النافذة لتلقي الخدمة :{service.name}",
        )
        self.assertEqual(
            Notification.objects.first().title,
            service.agency.municipality.name,
        )

    def test_push_notifications_skip_single_enactive_reservations(self):
        service = baker.make(
            "etickets_v2.Service",
            name="service 1",
            agency=self.agency,
            current_ticket=25,
            last_booked_ticket=50,
        )
        baker.make(
            "etickets_v2.Reservation",
            service=service,
            ticket_num=26,
            is_active=False,  # skip this one
        )
        baker.make(
            "etickets_v2.Reservation",
            service=service,
            ticket_num=27,
            is_active=True,  # notify this one
        )
        self.assertEqual(Notification.objects.count(), 0)
        response = self.client.post(
            reverse(
                "backend:etickets_v2:service-send_notifications",
                args=[self.municipality.pk, self.agency.pk, service.pk],
            ),
            {},
            format="json",
            HTTP_AUTHORIZATION=f"Api-Key {self.key}",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(
            Notification.objects.first().body,
            f"أمامك شخص واحد في صف خدمة {service.name}",
        )
        self.assertEqual(
            Notification.objects.first().title,
            service.agency.municipality.name,
        )

    def test_push_notifications_skip_multiple_enactive_reservations(self):
        """assert notifications created for last 5 reservations on a local server PUT"""
        for i in range(4):
            baker.make(
                "etickets_v2.Reservation",
                service=self.service,
                ticket_num=self.service.current_ticket + i,
                is_active=True,
            )
        for i in range(2):
            baker.make(
                "etickets_v2.Reservation",
                _quantity=3,
                service=self.service,
                is_active=False,
            )

        notifications_count = lambda: Notification.objects.count()
        self.assertEqual(notifications_count(), 0)
        response = self.client.post(
            reverse(
                "backend:etickets_v2:service-send_notifications",
                args=[self.municipality.pk, self.agency.pk, self.service.pk],
            ),
            {},
            format="json",
            HTTP_AUTHORIZATION=f"Api-Key {self.key}",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(notifications_count(), 4)
        self.assertEqual(
            Notification.objects.last().body,
            f"يرجى التقدم إلى النافذة لتلقي الخدمة :{self.service.name}",
        )

    def test_push_notifications_without_token(self):
        notifications_count = lambda: Notification.objects.count()
        self.assertEqual(notifications_count(), 0)
        response = self.client.post(
            reverse(
                "backend:etickets_v2:service-send_notifications",
                args=[self.municipality.pk, self.agency.pk, self.service.pk],
            ),
            {},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(notifications_count(), 0)

    def test_update_service_not_updating_without_token_or_permission(
        self,
    ):  # PUT /id no auth
        text = "other"
        data = {"description": text, "name": self.service.name}
        response = self.client.put(
            reverse(
                "backend:etickets_v2:service",
                args=[self.municipality.pk, self.agency.pk, self.service.pk],
            ),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate_manager_test
    def test_create_service_with_prefix(self):  # POST
        data1 = {
            "name": "string 1",
            "description": "string",
            "is_active": "true",
            "last_booked_ticket": 0,
            "current_ticket": 0,
            "created_by": 0,
            "avg_time_per_person": 8,
            "agency": self.agency.id,
        }
        data2 = {
            "name": "string 2",
            "description": "string",
            "is_active": "true",
            "last_booked_ticket": 0,
            "current_ticket": 0,
            "created_by": 0,
            "avg_time_per_person": 8,
            "agency": self.agency.id,
        }
        response1 = self.client.post(
            reverse(
                "backend:etickets_v2:services",
                args=[self.municipality.pk, self.agency.pk],
            ),
            data1,
            format="json",
        )
        response2 = self.client.post(
            reverse(
                "backend:etickets_v2:services",
                args=[self.municipality.pk, self.agency.pk],
            ),
            data2,
            format="json",
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response1.data["name"][1], "-")
        self.assertEqual(response1.data["name"][0], "ا")
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.data["name"][1], "-")
        self.assertEqual(response2.data["name"][0], "ب")
        self.assertNotEqual(response2.data["name"][0], response1.data["name"][0])

    @authenticate_manager_test
    def test_create_service_with_same_name_should_raise_error(self):  # POST
        data = {
            "name": "string",
            "description": "string",
            "is_active": "true",
            "last_booked_ticket": 0,
            "current_ticket": 0,
            "created_by": 0,
            "avg_time_per_person": 8,
            "agency": self.agency.id,
        }

        response1 = self.client.post(
            reverse(
                "backend:etickets_v2:services",
                args=[self.municipality.pk, self.agency.pk],
            ),
            data,
            format="json",
        )

        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        with self.assertRaises(ValidationError):
            self.client.post(
                reverse(
                    "backend:etickets_v2:services",
                    args=[self.municipality.pk, self.agency.pk],
                ),
                data,
                format="json",
            )
