
import unittest

from workflow import create_workflow
from models import StepStatus
from state_manager import mark_outcome_unknown
from reservation_service import (
    ReservationService,
    ReservationStatus,
    ReservationTimeout,
)
from recovery_engine import (
    get_idempotency_key,
    reconcile_reservation,
)

from recovery_engine import handle_inventory_version_change
from models import StepStatus


class TestRecoveryEngine(unittest.TestCase):

    def setUp(self):
        self.workflow = create_workflow("order-001", 17)
        self.service = ReservationService()
        self.step_name = "reserve_inventory"
        self.key = get_idempotency_key(
            self.workflow, self.step_name
        )

    def test_reconcile_successful_reservation_after_timeout(self):
        # External service succeeds, but our application times out.
        with self.assertRaises(ReservationTimeout):
            self.service.create_reservation(
                self.key, 2, simulate_timeout=True
            )

        mark_outcome_unknown(self.workflow, self.step_name)

        result = reconcile_reservation(
            self.workflow, self.step_name, self.service
        )

        self.assertEqual(result, "confirmed")

        self.assertEqual(
            self.workflow.steps[self.step_name].status,
            StepStatus.COMPLETED
        )

        # The original reservation still exists only once.
        self.assertEqual(len(self.service.reservations), 1)

    def test_reconcile_failed_reservation(self):
        self.service.create_reservation(
            self.key, 2, simulate_failure=True
        )

        mark_outcome_unknown(self.workflow, self.step_name)

        result = reconcile_reservation(
            self.workflow, self.step_name, self.service
        )

        self.assertEqual(result, "failed")

        self.assertEqual(
            self.workflow.steps[self.step_name].status,
            StepStatus.FAILED
        )

    def test_reconcile_reservation_not_found(self):
        mark_outcome_unknown(self.workflow, self.step_name)

        result = reconcile_reservation(
            self.workflow, self.step_name, self.service
        )

        self.assertEqual(result, "not_found")

        self.assertEqual(
            self.workflow.steps[self.step_name].status,
            StepStatus.OUTCOME_UNKNOWN
        )

    def test_inventory_version_change_invalidates_stale_steps(self):
        for step in self.workflow.steps.values():
            step.status = StepStatus.COMPLETED

        self.workflow.steps["reserve_inventory"].status = (
            StepStatus.OUTCOME_UNKNOWN
        )

        invalidated = handle_inventory_version_change(
            self.workflow, 18
        )

        self.assertEqual(self.workflow.inventory_version, 18)

        self.assertEqual(
            set(invalidated),
            {
                "retrieve_inventory",
                "calculate_plan",
                "generate_shipping_label",
                "notify_customer",
            }
        )

        self.assertEqual(
            self.workflow.steps["reserve_inventory"].status,
            StepStatus.OUTCOME_UNKNOWN
        )

if __name__ == "__main__":
    unittest.main()
