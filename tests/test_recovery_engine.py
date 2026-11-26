import unittest

from workflow import create_workflow
from models import StepStatus, ResultValidity
from state_manager import mark_outcome_unknown, mark_completed
from reservation_service import (
    ReservationService,
    ReservationTimeout,
)
from recovery_engine import (
    get_idempotency_key,
    reconcile_reservation,
    handle_inventory_version_change,
    recover_workflow,
)


class TestRecoveryEngine(unittest.TestCase):

    def setUp(self):
        self.workflow = create_workflow("order-001", 17)
        self.service = ReservationService()
        self.step_name = "reserve_inventory"
        self.key = get_idempotency_key(
            self.workflow, self.step_name
        )

    def test_reconcile_successful_reservation_after_timeout(self):
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
            step.validity = ResultValidity.VALID

        self.workflow.steps["reserve_inventory"].status = (
            StepStatus.OUTCOME_UNKNOWN
        )
        self.workflow.steps["reserve_inventory"].validity = (
            ResultValidity.UNKNOWN
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
                "reserve_inventory",
                "generate_shipping_label",
                "notify_customer",
            }
        )

        self.assertEqual(
            self.workflow.steps["retrieve_inventory"].validity,
            ResultValidity.STALE
        )

        self.assertEqual(
            self.workflow.steps["retrieve_inventory"].status,
            StepStatus.COMPLETED
        )

        self.assertEqual(
            self.workflow.steps["reserve_inventory"].status,
            StepStatus.OUTCOME_UNKNOWN
        )

    def test_recovery_after_successful_reservation_timeout(self):
        with self.assertRaises(ReservationTimeout):
            self.service.create_reservation(
                self.key, 2, simulate_timeout=True
            )

        mark_completed(
            self.workflow, "retrieve_inventory", {"stock": 50}
        )
        mark_completed(
            self.workflow, "calculate_plan", {"quantity": 2}
        )
        mark_outcome_unknown(self.workflow, self.step_name)

        result = recover_workflow(
            self.workflow, self.service, 17
        )

        self.assertEqual(
            self.workflow.steps[self.step_name].status,
            StepStatus.COMPLETED
        )
        self.assertEqual(
            result["ready_steps"],
            ["generate_shipping_label"]
        )
        self.assertEqual(result["unresolved_steps"], [])

    def test_recovery_after_inventory_version_change(self):
        with self.assertRaises(ReservationTimeout):
            self.service.create_reservation(
                self.key, 2, simulate_timeout=True
            )

        mark_completed(
            self.workflow, "retrieve_inventory", {"stock": 50}
        )
        mark_completed(
            self.workflow, "calculate_plan", {"quantity": 2}
        )
        mark_outcome_unknown(self.workflow, self.step_name)

        result = recover_workflow(
            self.workflow, self.service, 18
        )

        self.assertEqual(self.workflow.inventory_version, 18)
        self.assertEqual(
            self.workflow.steps[self.step_name].status,
            StepStatus.COMPLETED
        )
        self.assertEqual(
            result["ready_steps"],
            ["retrieve_inventory"]
        )
        self.assertNotIn(
            "generate_shipping_label",
            result["ready_steps"]
        )


if __name__ == "__main__":
    unittest.main()
