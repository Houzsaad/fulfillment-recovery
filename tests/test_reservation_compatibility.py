
import unittest

from workflow import create_workflow
from models import StepStatus, ResultValidity
from state_manager import mark_completed
from reservation_service import (
    ReservationService,
    ReleaseStatus,
)
from recovery_engine import (
    recover_workflow,
    get_idempotency_key,
)


class TestReservationRecovery(unittest.TestCase):

    def setUp(self):
        self.workflow = create_workflow("order-001", 18)
        self.service = ReservationService()

        self.key = get_idempotency_key(
            self.workflow, "reserve_inventory"
        )

        self.service.create_reservation(self.key, quantity=2)

        mark_completed(
            self.workflow,
            "retrieve_inventory",
            {"stock": 50},
        )

        mark_completed(
            self.workflow,
            "calculate_plan",
            {"quantity": 2},
        )

        mark_completed(
            self.workflow,
            "reserve_inventory",
            {"quantity": 2},
        )

    def test_compatible_reservation_remains_valid(self):
        self.workflow.steps["reserve_inventory"].validity = (
            ResultValidity.STALE
        )

        result = recover_workflow(
            self.workflow, self.service, 18
        )

        self.assertEqual(
            result["reconciliation"]["reservation_compatibility"],
            "compatible",
        )

        self.assertEqual(
            self.workflow.steps["reserve_inventory"].validity,
            ResultValidity.VALID,
        )

    def test_incompatible_reservation_is_released(self):
        mark_completed(
            self.workflow,
            "calculate_plan",
            {"quantity": 5},
        )

        self.workflow.steps["reserve_inventory"].validity = (
            ResultValidity.STALE
        )

        result = recover_workflow(
            self.workflow, self.service, 18
        )

        reservation = self.service.get_reservation(self.key)

        self.assertEqual(
            reservation.release_status,
            ReleaseStatus.RELEASED,
        )

        self.assertEqual(
            result["reconciliation"]["reservation_compatibility"],
            "released_re_reservation_required",
        )

        self.assertNotIn(
            "generate_shipping_label",
            result["ready_steps"],
        )

    def test_failed_release_blocks_shipping(self):
        mark_completed(
            self.workflow,
            "calculate_plan",
            {"quantity": 5},
        )

        self.workflow.steps["reserve_inventory"].validity = (
            ResultValidity.STALE
        )

        # Simulate a provider that rejects the release.
        original_release = self.service.release_reservation

        def failed_release(key):
            return original_release(key, simulate_failure=True)

        self.service.release_reservation = failed_release

        result = recover_workflow(
            self.workflow, self.service, 18
        )

        self.assertEqual(
            result["reconciliation"]["reservation_compatibility"],
            "release_failed",
        )

        self.assertNotIn(
            "generate_shipping_label",
            result["ready_steps"],
        )


if __name__ == "__main__":
    unittest.main()
