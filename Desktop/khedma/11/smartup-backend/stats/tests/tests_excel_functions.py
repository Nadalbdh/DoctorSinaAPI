import os
from datetime import date, datetime, time, timedelta

from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from django.utils import timezone
from freezegun import freeze_time
from model_bakery import baker

from backend.admin import MunicipalityAdmin
from backend.models import Complaint, Municipality, News
from backend.serializers.serializers import MunicipalitySerializer
from backend.tests.test_base import ElBaladiyaAPITest
from etickets_v2.models import Agency, Reservation, Service
from settings.settings import MEDIA_ROOT
from stats.functions import (
    days_since_last_instance,
    get_avg_final_response,
    get_avg_first_response,
    get_closed_instance_entire_timeline,
    get_count_status,
    get_count_total,
    get_digital_tickets_count,
    get_percentage_closed_instances,
    get_percentage_closed_instances_in_less_than_specific_period,
    get_sum_days_difference_for_closed_operations_final_response,
    get_sum_days_difference_for_first_response,
)
from stats.tasks import export_kpis_as_excel

TODAY = "2023-05-12"


@freeze_time(TODAY)
class ExcelTest(ElBaladiyaAPITest):
    def setUp(self):
        super().setUp()
        folder_path = "/backend/media/internal"
        os.makedirs(folder_path, exist_ok=True)
        self.user = baker.make("User", username="12345678")
        self.complaint1 = Complaint.objects.create(
            created_by=self.user,
            municipality=self.municipality,
        )
        self.complaint1.created_at = datetime.now() - timedelta(days=15)
        self.complaint1.save()
        self.complaint2 = Complaint.objects.create(
            created_by=self.user,
            municipality=self.municipality,
        )
        self.complaint2.created_at = datetime.now() - timedelta(days=14)
        self.complaint2.save()
        self.complaint3 = Complaint.objects.create(
            created_by=self.user,
            municipality=self.municipality,
        )
        self.complaint3.created_at = datetime.now() - timedelta(days=13)
        self.complaint3.save()

        # Add operation updates for complaints
        self.complaint1_op1 = self.complaint1.operation_updates.create(
            status="RECIEVED",
        )
        self.complaint1_op1.created_at = datetime.now() - timedelta(days=11)
        self.complaint1_op1.save()
        self.complaint1_op2 = self.complaint1.operation_updates.create(
            status="PROCESSING",
        )
        self.complaint1_op2.created_at = datetime.now() - timedelta(days=9)
        self.complaint1_op2.save()
        self.complaint2_op1 = self.complaint2.operation_updates.create(
            status="NOT_CLEAR",
        )
        self.complaint2_op1.created_at = datetime.now() - timedelta(days=7)
        self.complaint2_op1.save()
        self.complaint3_op1 = self.complaint3.operation_updates.create(
            status="PROCESSING",
        )
        self.complaint3_op1.created_at = datetime.now() - timedelta(days=5)
        self.complaint3_op1.save()
        self.complaint3_op2 = self.complaint3.operation_updates.create(
            status="INVALID",
        )
        self.complaint3_op2.created_at = datetime.now() - timedelta(days=2)
        self.complaint3_op2.save()

        self.complaint1.operation_updates.set(
            [self.complaint1_op1, self.complaint1_op2]
        )
        self.complaint2.operation_updates.set([self.complaint2_op1])
        self.complaint3.operation_updates.set(
            [self.complaint3_op1, self.complaint3_op2]
        )

    def test_get_count_status(self):
        count_list = [
            {'status': 'ACCEPTED', 'count': 5},
            {'status': 'REJECTED', 'count': 3},
            {'status': 'PPROCESSING', 'count': 2},
        ]
        self.assertEqual(get_count_status(['ACCEPTED'], count_list), 5)
        self.assertEqual(get_count_status(['REJECTED', 'ACCEPTED'], count_list), 8)
        self.assertEqual(get_count_status(['INVALID'], count_list), 0)

    def test_get_count_total(self):
        count_list = [
            {'status': 'ACCEPTED', 'count': 5},
            {'status': 'REJECTED', 'count': 3},
            {'status': 'PENDING', 'count': 2},
        ]
        self.assertEqual(get_count_total(count_list), 10)

    def test_get_percentage_closed_instances(self):
        count_list = [
            {'status': 'ACCEPTED', 'count': 5},
            {'status': 'REJECTED', 'count': 2},
            {'status': 'PROCESSING', 'count': 1},
            {'status': 'INVALID', 'count': 2},
        ]
        self.assertEqual(get_percentage_closed_instances(count_list), 90.0)

    def test_get_closed_instance_entire_timeline(self):
        created_at = datetime(2023, 4, 1)
        result = get_closed_instance_entire_timeline(
            Complaint, self.municipality.id, created_at
        )
        self.assertEqual(len(result), 3)
        self.assertIn(
            (
                self.complaint1.created_at.astimezone(timezone.utc),
                self.complaint1_op1.created_at.astimezone(timezone.utc),
                self.complaint1_op2.created_at.astimezone(timezone.utc),
                "RECIEVED",
                "PROCESSING",
            ),
            result,
        )
        self.assertIn(
            (
                self.complaint2.created_at.astimezone(timezone.utc),
                None,
                self.complaint2_op1.created_at.astimezone(timezone.utc),
                None,
                "NOT_CLEAR",
            ),
            result,
        )
        self.assertIn(
            (
                self.complaint3.created_at.astimezone(timezone.utc),
                self.complaint3_op1.created_at.astimezone(timezone.utc),
                self.complaint3_op2.created_at.astimezone(timezone.utc),
                "PROCESSING",
                "INVALID",
            ),
            result,
        )

    def test_get_sum_days_difference_for_closed_operations_final_response(self):
        items = [
            (datetime(2022, 5, 1), None, datetime(2022, 5, 2), 'ACCEPTED', 'REJECTED'),
            (
                datetime(2022, 5, 3),
                datetime(2022, 5, 4),
                datetime(2022, 5, 5),
                'REJECTED',
                'ACCEPTED',
            ),
            (
                datetime(2022, 5, 6),
                datetime(2022, 5, 7),
                datetime(2022, 5, 8),
                'NOT_CLEAR',
                'PROCESSING',
            ),
            (datetime(2022, 5, 9), None, datetime(2022, 5, 10), 'INVALID', 'NOT_CLEAR'),
        ]
        self.assertEqual(
            get_sum_days_difference_for_closed_operations_final_response(items), 4
        )

    def test_get_sum_days_difference_for_first_response(self):
        items = [
            (
                datetime(2022, 5, 3),
                datetime(2022, 5, 4),
                datetime(2022, 5, 5),
                'REJECTED',
                'CLOSED',
            ),
            (
                datetime(2022, 5, 6),
                datetime(2022, 5, 7),
                datetime(2022, 5, 8),
                'NOT_CLEAR',
                'PROCESSING',
            ),
            (
                datetime(2022, 5, 9),
                datetime(2022, 5, 10),
                datetime(2022, 5, 10),
                'INVALID',
                'CLOSED',
            ),
        ]
        self.assertEqual(get_sum_days_difference_for_first_response(items), 3)

    def test_get_avg_first_response(self):
        created_at = date(2023, 4, 1)
        avg_first_response = get_avg_first_response(
            Complaint, self.municipality.id, created_at
        )
        self.assertEqual(avg_first_response, 4)

    def test_get_avg_final_response(self):
        created_at = date(2023, 4, 1)
        avg_final_response = get_avg_final_response(
            Complaint, self.municipality.id, created_at
        )
        self.assertEqual(avg_final_response, 6)

    def test_get_percentage_closed_instances_in_less_than_specific_period(self):
        # Test for period of 10 days
        percentage = get_percentage_closed_instances_in_less_than_specific_period(
            Complaint,
            [{'status': 'ACCEPTED', 'count': 5}, {'status': 'REJECTED', 'count': 5}],
            self.municipality.id,
            10,
        )
        self.assertEqual(percentage, 20.0)

        # Test for period of 5 days
        percentage = get_percentage_closed_instances_in_less_than_specific_period(
            Complaint,
            [{'status': 'NOT_CLEAR', 'count': 8}, {'status': 'ACCEPTED', 'count': 2}],
            self.municipality.id,
            3,
        )
        self.assertEqual(percentage, 10.0)

    def testdays_since_last_instance(self):
        News.objects.create(
            municipality=self.municipality,
            published_at=datetime.now() - timedelta(days=3),
            body="body",
        )
        News.objects.create(
            municipality=self.municipality,
            published_at=datetime.now(),
            body="body",
        )
        # Test with News model
        days_since_last_news = days_since_last_instance(News, self.municipality.id)
        self.assertEqual(days_since_last_news, 0)

        # Test with invalid model
        days_since_invalid_model = days_since_last_instance(None, self.municipality.id)
        self.assertIsNone(days_since_invalid_model)

    def test_get_digital_tickets_count(self):
        agency = Agency.objects.create(
            name="Test Agency",
            municipality=self.municipality,
            weekday_first_start=time(8, 0),
            weekday_first_end=time(12, 0),
            weekday_second_start=time(14, 0),
            weekday_second_end=time(17, 0),
        )
        service = Service.objects.create(name="Test Service", agency=agency)
        Reservation.objects.create(
            created_by=self.user,
            service=service,
            ticket_num=1,
            is_physical=False,
        )
        Reservation.objects.create(
            created_by=self.user,
            service=service,
            ticket_num=2,
            is_physical=False,
        )
        Reservation.objects.create(
            created_by=self.user,
            service=service,
            ticket_num=3,
            is_physical=False,
        )
        digital_tickets_count = get_digital_tickets_count(self.municipality.id)

        self.assertEqual(digital_tickets_count, 3)

    # def test_export_kpis_as_excel(self):
    #     queryset = Municipality.objects.filter(is_active=True)
    #     serializer = MunicipalitySerializer(queryset, many=True)
    #     serialized_data = serializer.data
    #     created_at = date(2023, 4, 1)
    #     result = export_kpis_as_excel.delay(serialized_data, created_at)
    #     file_path = result.get()
    #     self.assertIsNotNone(file_path)

    #     base_name = "latest_kpis"
    #     file_name = f"{base_name}_{created_at.strftime('%Y-%m-%dT%H:%M:%S')}.xlsx"
    #     expected_file_path = os.path.join(MEDIA_ROOT, "internal", file_name)

    #     self.assertEqual(file_path, expected_file_path)

    #     self.assertTrue(os.path.isfile(file_path))

    def tearDown(self):
        # Define the path to the "to_print" directory
        path = os.path.join(MEDIA_ROOT, "internal")
        # Loop through all the files in the directory
        for filename in os.listdir(path):
            file_path = os.path.join(path, filename)
            # Check if the file is a .png file
            if filename.endswith('.xlsx'):
                # Delete the file
                os.remove(file_path)
