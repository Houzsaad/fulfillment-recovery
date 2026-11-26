import unittest

from workflow import create_workflow
from models import StepStatus, ResultValidity
from state_manager import (
    mark_running,
    mark_completed,
    mark_outcome_unknown,
    invalidate_step,
)


class TestStateManager(unittest.TestCase):

    def setUp(self):
        self.workflow = create_workflow("order-001", 17)

    def test_mark_running(self):
        mark_running(self.workflow, "reserve_inventory")

        self.assertEqual(
            self.workflow.steps["reserve_inventory"].status,
            StepStatus.RUNNING
        )

    def test_mark_completed(self):
        output = {"available_stock": 50}

        mark_completed(self.workflow, "retrieve_inventory", output)

        step = self.workflow.steps["retrieve_inventory"]

        self.assertEqual(step.status, StepStatus.COMPLETED)
        self.assertEqual(step.output, output)

    def test_mark_outcome_unknown(self):
        mark_outcome_unknown(self.workflow, "reserve_inventory")

        self.assertEqual(
            self.workflow.steps["reserve_inventory"].status,
            StepStatus.OUTCOME_UNKNOWN
        )

    def test_invalidate_step(self):
        step = self.workflow.steps["retrieve_inventory"]

        mark_completed(
            self.workflow,
            "retrieve_inventory",
            {"stock": 50}
        )

        invalidate_step(self.workflow, "retrieve_inventory")

        self.assertEqual(step.status, StepStatus.COMPLETED)
        self.assertEqual(step.validity, ResultValidity.STALE)
        self.assertEqual(step.output, {"stock": 50})


if __name__ == "__main__":
    unittest.main()