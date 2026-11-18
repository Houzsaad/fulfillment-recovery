from models import Workflow, WorkflowStep, StepStatus


def create_workflow(workflow_id: str, inventory_version: int) -> Workflow:
    workflow = Workflow(
        workflow_id=workflow_id,
        inventory_version=inventory_version,
    )

    workflow.steps = {
        "retrieve_inventory": WorkflowStep(
            name="retrieve_inventory",
        ),

        "calculate_plan": WorkflowStep(
            name="calculate_plan",
            dependencies=["retrieve_inventory"],
            input_version=inventory_version,
        ),

        "reserve_inventory": WorkflowStep(
            name="reserve_inventory",
            dependencies=["calculate_plan"],
            input_version=inventory_version,
        ),

        "generate_shipping_label": WorkflowStep(
            name="generate_shipping_label",
            dependencies=["reserve_inventory"],
        ),

        "notify_customer": WorkflowStep(
            name="notify_customer",
            dependencies=["generate_shipping_label"],
        ),
    }

    return workflow