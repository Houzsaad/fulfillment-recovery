import unittest

from reservation_service import (
    ReservationService,
    ReservationStatus,
    ReservationTimeout,
)


class TestReservationService(unittest.TestCase):

    def setUp(self):
        self.service = ReservationService()
        self.key = "order-001-reservation"

    def test_successful_reservation(self):
        reservation = self.service.create_reservation(
            self.key, 2
        )

        self.assertEqual(
            reservation.status,
            ReservationStatus.CONFIRMED
        )

    def test_duplicate_request_returns_existing_reservation(self):
        first = self.service.create_reservation(self.key, 2)
        second = self.service.create_reservation(self.key, 2)

        self.assertIs(first, second)
        self.assertEqual(len(self.service.reservations), 1)

    def test_timeout_preserves_external_reservation(self):
        with self.assertRaises(ReservationTimeout):
            self.service.create_reservation(
                self.key, 2, simulate_timeout=True
            )

        reservation = self.service.get_reservation(self.key)

        self.assertIsNotNone(reservation)
        self.assertEqual(
            reservation.status,
            ReservationStatus.CONFIRMED
        )

    def test_failed_reservation(self):
        reservation = self.service.create_reservation(
            self.key, 2, simulate_failure=True
        )

        self.assertEqual(
            reservation.status,
            ReservationStatus.FAILED
        )

    def test_invalid_quantity(self):
        with self.assertRaises(ValueError):
            self.service.create_reservation(self.key, 0)


if __name__ == "__main__":
    unittest.main()
