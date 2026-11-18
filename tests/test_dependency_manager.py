import unittest

from workflow import create_workflow
from dependency_manager import get_downstream_steps

from models import StepStatus
from dependency_manager import invalidate_downstream_steps

class TestDependencyManager(unittest.TestCase):

    def setUp(self):
        self.workflow = create_workflow("order-001", 17)

    def test_get_downstream_steps(self):
        affected = get_downstream_steps(
            self.workflow,
            "calculate_plan"
        )

        expected = [
            "reserve_inventory",
            "generate_shipping_label",
            "notify_customer"
        ]

        self.assertEqual(affected, expected)

    def test_first_step_affects_every_downstream_step(self):
        affected = get_downstream_steps(
            self.workflow,
            "retrieve_inventory"
        )

        self.assertEqual(len(affected), 4)

    def test_last_step_has_no_downstream_steps(self):
        affected = get_downstream_steps(
            self.workflow,
            "notify_customer"
        )

        self.assertEqual(affected, [])

    def test_invalidate_downstream_steps(self):

        for step in self.workflow.steps.values():
            step.status = StepStatus.COMPLETED

        affected = invalidate_downstream_steps(
            self.workflow,
            "retrieve_inventory"
        )

        self.assertEqual(len(affected), 4)

        self.assertEqual(
            self.workflow.steps["retrieve_inventory"].status,
            StepStatus.COMPLETED
        )

        for name in affected:
            self.assertEqual(
                self.workflow.steps[name].status,
                StepStatus.INVALIDATED
            )

if __name__ == "__main__":
    unittest.main()