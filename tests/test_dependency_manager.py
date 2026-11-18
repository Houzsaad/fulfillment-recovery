import unittest

from workflow import create_workflow
from dependency_manager import get_downstream_steps


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


if __name__ == "__main__":
    unittest.main()