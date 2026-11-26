
import unittest

from reservation_service import (
    ReservationService,
    ReservationStatus,
    ReleaseStatus,
    ReservationReleaseTimeout,
)


class TestReservationCompensation(unittest.TestCase):

    def setUp(self):
        self.service = ReservationService()
        self.key = "order-001:reserve_inventory"

        self.service.create_reservation(
            self.key,
            quantity=2,
        )

    def test_successful_release(self):
        reservation = self.service.release_reservation(self.key)

        self.assertEqual(
            reservation.status,
            ReservationStatus.CONFIRMED,
        )
        self.assertEqual(
            reservation.release_status,
            ReleaseStatus.RELEASED,
        )

    def test_failed_release(self):
        reservation = self.service.release_reservation(
            self.key,
            simulate_failure=True,
        )

        self.assertEqual(
            reservation.release_status,
            ReleaseStatus.FAILED,
        )
        self.assertEqual(
            reservation.status,
            ReservationStatus.CONFIRMED,
        )

    def test_release_timeout(self):
        with self.assertRaises(ReservationReleaseTimeout):
            self.service.release_reservation(
                self.key,
                simulate_timeout=True,
            )

        reservation = self.service.get_reservation(self.key)

        self.assertEqual(
            reservation.release_status,
            ReleaseStatus.RELEASED,
        )

    def test_repeated_release_does_not_duplicate_operation(self):
        first = self.service.release_reservation(self.key)
        second = self.service.release_reservation(self.key)

        self.assertIs(first, second)
        self.assertEqual(
            second.release_status,
            ReleaseStatus.RELEASED,
        )


if __name__ == "__main__":
    unittest.main()
