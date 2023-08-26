from model_bakery import baker

from backend.enum import RequestStatus
from backend.models import OperationUpdate, Reservation

from .test_base import TestBase


class ReservationTest(TestBase):
    def test_create_reservation_limit(self):
        """
        Scenario:
            1) Create an appointment with 2 maximum reservation
            2) Create 2 reservation, both should succeed
            3) Create a third, and it should fail
            4) Decline an old reservation.
            5) Create a new reservation, and it should succeed
        """
        app = baker.make("backend.appointment", max_reservations=2)

        self.assertEqual(Reservation.objects.all().count(), 0)

        baker.make("backend.reservation", appointment_id=1)
        self.assertEqual(Reservation.objects.all().count(), 1)

        rdv_to_decline = baker.make("backend.reservation", appointment_id=1)
        self.assertEqual(Reservation.objects.all().count(), 2)

        baker.make("backend.reservation", appointment_id=1)
        self.assertEqual(Reservation.objects.all().count(), 2)

        rdv_to_decline.reservation_state_citizen = RequestStatus.REJECTED
        rdv_to_decline.save()
        baker.make("backend.reservation", appointment_id=1)
        self.assertEqual(Reservation.objects.all().count(), 3)

    def test_create_reservation_operation_update(self):
        self.assertEqual(OperationUpdate.objects.all().count(), 0)
        app = baker.make("backend.appointment", max_reservations=2)
        baker.make("backend.reservation", appointment_id=app.id)
        self.assertEqual(OperationUpdate.objects.all().count(), 2)
