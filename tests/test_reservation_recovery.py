
import unittest

from workflow import create_workflow
from models import ResultValidity
from state_manager import mark_completed
from reservation_service import ReservationService
from recovery_engine import check_reservation_compatibility


class TestReservationCompatibility(unittest.TestCase):

    def setUp(self):
        self.workflow = create_workflow("order-001", 17)
        self.service = ReservationService()

        self.reservation = self.service.create_reservation(
            "order-001:reserve_inventory",
            quantity=2,
        )

    def test_compatible_reservation(self):
        mark_completed(
            self.workflow,
            "calculate_plan",
            {"quantity": 2},
        )

        result = check_reservation_compatibility(
            self.workflow,
            self.reservation,
        )

        self.assertEqual(result, "compatible")

    def test_incompatible_reservation(self):
        mark_completed(
            self.workflow,
            "calculate_plan",
            {"quantity": 5},
        )

        result = check_reservation_compatibility(
            self.workflow,
            self.reservation,
        )

        self.assertEqual(result, "incompatible")

    def test_stale_plan_cannot_be_used(self):
        mark_completed(
            self.workflow,
            "calculate_plan",
            {"quantity": 2},
        )

        self.workflow.steps["calculate_plan"].validity = (
            ResultValidity.STALE
        )

        result = check_reservation_compatibility(
            self.workflow,
            self.reservation,
        )

        self.assertEqual(result, "plan_unavailable")


if __name__ == "__main__":
    unittest.main()
