import unittest

from workflow import create_workflow
from models import StepStatus, ResultValidity
from state_manager import mark_completed, mark_outcome_unknown
from reservation_service import (
    ReservationService,
    ReservationTimeout,
    ReleaseStatus,
)
from recovery_engine import (
    recover_workflow,
    get_idempotency_key,
)


class TestInventoryChangeRecovery(unittest.TestCase):

    def setUp(self):
        self.workflow = create_workflow("order-001", 17)
        self.service = ReservationService()

        self.key = get_idempotency_key(
            self.workflow, "reserve_inventory"
        )

    def test_uncertain_reservation_after_inventory_change(self):
        # Complete the original inventory and plan steps.
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

        # External reservation succeeds, but its response times out.
        with self.assertRaises(ReservationTimeout):
            self.service.create_reservation(
                self.key,
                quantity=2,
                simulate_timeout=True,
            )

        mark_outcome_unknown(
            self.workflow,
            "reserve_inventory",
        )

        # Inventory changes from version 17 to 18.
        result = recover_workflow(
            self.workflow,
            self.service,
            current_inventory_version=18,
        )

        self.assertEqual(
            result["reconciliation"]["reserve_inventory"],
            "confirmed",
        )

        # The original reservation is confirmed but still stale.
        reservation_step = self.workflow.steps["reserve_inventory"]

        self.assertEqual(
            reservation_step.status,
            StepStatus.COMPLETED,
        )

        self.assertEqual(
            reservation_step.validity,
            ResultValidity.STALE,
        )

        # Shipping must not proceed while the plan is stale.
        self.assertNotIn(
            "generate_shipping_label",
            result["ready_steps"],
        )

        # A fresh plan is now calculated for inventory version 18.
        self.workflow.steps["retrieve_inventory"].input_version = 18
        self.workflow.steps["calculate_plan"].input_version = 18

        mark_completed(
            self.workflow,
            "retrieve_inventory",
            {"stock": 50},
        )

        mark_completed(
            self.workflow,
            "calculate_plan",
            {"quantity": 5},
        )

        # Recover again: old reservation is incompatible and must be released.
        result = recover_workflow(
            self.workflow,
            self.service,
            current_inventory_version=18,
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


if __name__ == "__main__":
    unittest.main()
