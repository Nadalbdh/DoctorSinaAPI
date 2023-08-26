import math
import os
from datetime import date, datetime, timedelta

from django.contrib.contenttypes.models import ContentType
from django.db.models import signals
from django.urls import reverse
from freezegun import freeze_time
from model_bakery import baker
from rest_framework import status

from backend.enum import RequestStatus
from backend.models import (
    Comment,
    Complaint,
    Dossier,
    OperationUpdate,
    SubjectAccessRequest,
)
from backend.tests.baker import add_status
from backend.tests.test_base import authenticate_manager_test, ElBaladiyaAPITest
from etickets_v2.models import Service
from stats.functions import (
    _calculate_avg_response,
    _get_instance_timeline_and_status,
    _get_objects_count,
    _get_sum_days_difference,
    _get_timeline_and_status,
    _status_count,
    get_officer_kpi_dashboard,
    record_eticket_performance,
    record_operation_performance,
)

TODAY = "2022-09-30"


@freeze_time(TODAY)
class StatsTest(ElBaladiyaAPITest):
    def setUp(self):
        super().setUp()
        self.seed_models = [
            "Complaint",
            "Dossier",
            "SubjectAccessRequest",
            "Event",
            "News",
            "Report",
        ]
        folder_path = "/backend/media/internal"
        os.makedirs(folder_path, exist_ok=True)
        for idx, value in enumerate(self.seed_models):
            baker.make(
                f"backend.{value}", municipality=self.municipality, _quantity=idx + 2
            )

    @authenticate_manager_test
    def test_updatebles_from_endpoint(self):
        statuses = RequestStatus.get_statuses()
        updatable = ["complaints", "dossiers", "subject_access_requests"]

        response = self.client.get(
            reverse("backend:stats:municipality", args=[self.municipality.id])
        )
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for i in updatable:
            self.assertEqual(len(data.get(i)), len(statuses))

    def test_get_unauthorized(self):
        response = self.client.get(
            reverse("backend:stats:municipality", args=[self.municipality.id])
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_sum_days(self):
        today = datetime.now()
        day_after = 10
        tomorrow = today + timedelta(days=day_after)
        self.assertEqual(
            _get_sum_days_difference(
                [[today, today, RequestStatus.ACCEPTED, RequestStatus.ACCEPTED]]
            ),
            0,
        )
        self.assertEqual(
            _get_sum_days_difference(
                [
                    [
                        TODAY + " 21:22:38.743689",
                        None,
                        None,
                        RequestStatus.RECEIVED,
                    ],
                    [
                        today,
                        tomorrow,
                        RequestStatus.ACCEPTED,
                        RequestStatus.ACCEPTED,
                    ],
                ]
            ),
            day_after,
        )

    def test_get_timeline_and_status(self):
        complaint_fields = _get_timeline_and_status(
            Complaint,
            municipality_id=self.municipality.id,
            created_at__month=date.today().month,
        )
        dossier_fields = _get_timeline_and_status(
            Dossier,
            municipality_id=self.municipality.id,
            created_at__month=date.today().month,
        )

        # been created at SetUp
        self.assertEqual(len(complaint_fields), 2)
        self.assertEqual(len(dossier_fields), 3)

        # assert date
        self.assertEqual(str(dossier_fields[0][0])[:10], TODAY)

    def test_get_objects_count(self):
        count = _get_objects_count(
            [Complaint, Complaint], municipality_id=self.municipality.pk
        )
        true_count = (
            Complaint.objects.filter(municipality_id=self.municipality.pk).count() * 2
        )
        self.assertEqual(count, true_count)

    def test_record_operation_performance(self):
        result = record_operation_performance(
            self.municipality, [Complaint, Comment, SubjectAccessRequest]
        )

        self.assertEqual(result.received_percentage, 100)

    def test_calculate_avg_response(self):
        self.assertEqual(
            _calculate_avg_response(0, 0), None
        )  # municipality has no updatable objects
        self.assertEqual(
            _calculate_avg_response(None, 10), None
        )  # municipality did no operation update
        self.assertEqual(_calculate_avg_response(50, 10), math.ceil(50 / 10))

    def test_get_instance_timeline_and_status(self):
        updatable_object = Complaint.objects.first()
        timeline = _get_instance_timeline_and_status(updatable_object)
        self.assertEqual(
            timeline,
            (
                updatable_object.created_at,
                None,
                None,
                updatable_object.last_operation_update.status,
            ),
        )

        add_status(updatable_object, RequestStatus.PROCESSING, "2021-05-15")
        add_status(updatable_object, RequestStatus.ACCEPTED, "2021-05-20")
        timeline = _get_instance_timeline_and_status(updatable_object)
        self.assertEqual(
            timeline,
            (
                updatable_object.created_at,
                updatable_object.operation_updates.all()[1].created_at,
                updatable_object.operation_updates.all()[1].status,
                updatable_object.last_operation_update.status,
            ),
        )

    def test_get_officer_kpi_dashboard(self):
        query = get_officer_kpi_dashboard(self.municipality.id)
        updatable_models = [
            (Complaint, "complaints"),
            (SubjectAccessRequest, "subject_access_requests"),
            (Dossier, "dossiers"),
            (Comment, "forum"),
        ]
        for model in updatable_models:
            expected_count = sum([i["count"] for i in query[model[1]]])
            actual_count = (
                model[0]
                .objects.filter(operation_updates__status=RequestStatus.RECEIVED)
                .count()
            )
            self.assertEqual(expected_count, actual_count)

    def test_get_officer_kpi_dashboard_not_counting_sub_comments(self):
        # create 1 comment
        parent = baker.make("backend.Comment", municipality=self.municipality)
        # create 2 subcomments
        baker.make(
            "backend.Comment",
            parent_comment=parent,
            parent_comment_id=parent.id,
            municipality=self.municipality,
            _quantity=2,
        )
        query = get_officer_kpi_dashboard(self.municipality.id)
        expected_count = sum([i["count"] for i in query["forum"]])
        self.assertEqual(expected_count, 1)

    @authenticate_manager_test
    def test__status_count(self):
        signals.post_save.disconnect(
            sender=OperationUpdate, dispatch_uid="sms-notify-update"
        )
        signals.post_save.disconnect(
            sender=OperationUpdate, dispatch_uid="push-notify-followers-on-update"
        )
        municipality = baker.make(
            "backend.Municipality",
        )
        baker.make("backend.complaint", municipality=municipality)
        complaint = baker.make("backend.complaint", municipality=municipality)
        contenttype = ContentType.objects.create(model=complaint)

        types = ["REJECTED", "INVALID", "NOT_CLEAR", "ACCEPTED"]
        operation_updates = [
            OperationUpdate.objects.create(
                status=status_type,
                content_type=contenttype,
                object_id=123,
                created_by=self.manager.user,
                operation=complaint,
            )
            for status_type in types
        ]

        baker.make(
            "backend.complaint",
            municipality=municipality,
            id=123,
            operation_updates=operation_updates,
        )

        expected_output = [
            {
                "status": "RECEIVED",
                "count": 2,  # complaint1 and complaint are received by default
            },
            {"status": "PROCESSING", "count": 0},
            {
                "status": "ACCEPTED",
                "count": 1,  # complaint2 has the last status = "ACCEPTED"
            },
            {"status": "REJECTED", "count": 0},
            {"status": "NOT_CLEAR", "count": 0},
            {"status": "INVALID", "count": 0},
        ]
        complaints = _status_count(Complaint, municipality_id=municipality.pk)
        self.assertEqual(complaints, expected_output)

    def test_record_eticket_performance(self):
        physical = 8
        digital = 20
        agency = baker.make("etickets_v2.Agency", municipality=self.municipality)
        baker.make(
            "etickets_v2.Service",
            agency=agency,
            last_booked_ticket=20,
            current_ticket=5,
            _quantity=5,
        )
        baker.make(
            "etickets_v2.Reservation",
            service=Service.objects.last(),
            is_physical=False,
            _quantity=digital,
        )
        baker.make(
            "etickets_v2.Reservation",
            service=Service.objects.first(),
            is_physical=True,
            _quantity=physical,
        )
        result = record_eticket_performance(agency)
        count_all_reservations = sum(
            [
                s.last_booked_ticket if s.last_booked_ticket else 0
                for s in Service.objects.all()
            ]
        )
        self.assertEqual(
            (physical / count_all_reservations) * 100,
            result.physical_reservation_percentage,
        )
        self.assertEqual(
            (digital / count_all_reservations) * 100,
            result.digital_reservation_percentage,
        )
        self.assertEqual(
            ((count_all_reservations - digital - physical) / count_all_reservations)
            * 100,
            result.not_digitized_reservation_percentage,
        )

        self.assertEqual(
            sum(
                [
                    result.not_digitized_reservation_percentage,
                    result.digital_reservation_percentage,
                    result.physical_reservation_percentage,
                ]
            ),
            100.0,
        )

        # TODO after margin this with push notifs
        # maybe you need to mock notifs handler I'm not sure
        # self.assertEqual(Notifications.objects.count(),Reservations.objects.count())
