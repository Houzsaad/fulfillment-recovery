from models import StepStatus
from reservation_service import ReservationStatus
from state_manager import mark_completed, mark_failed

from dependency_manager import get_downstream_steps
from state_manager import invalidate_step

def get_idempotency_key(workflow, step_name):
    return f"{workflow.workflow_id}:{step_name}"


def reconcile_reservation(workflow, step_name, service):
    step = workflow.steps[step_name]

    if step.status != StepStatus.OUTCOME_UNKNOWN:
        raise ValueError("Step does not have an uncertain outcome.")

    key = get_idempotency_key(workflow, step_name)

    reservation = service.get_reservation(key)

    if reservation is None:
        return "not_found"

    if reservation.status == ReservationStatus.CONFIRMED:
        mark_completed(
            workflow,
            step_name,
            {
                "idempotency_key": key,
                "quantity": reservation.quantity,
                "status": reservation.status.value,
            }
        )
        return "confirmed"

    if reservation.status == ReservationStatus.FAILED:
        mark_failed(workflow, step_name)
        return "failed"

    return "pending"


def handle_inventory_version_change(workflow, new_version):
    if new_version == workflow.inventory_version:
        return []

    workflow.inventory_version = new_version

    affected = set()

    for name, step in workflow.steps.items():
        if (
            step.input_version is not None
            and step.input_version != new_version
        ):
            affected.add(name)
            affected.update(
                get_downstream_steps(workflow, name)
            )

    # Never erase the record of an external reservation.
    protected_steps = {"reserve_inventory"}

    invalidated = []

    for name in workflow.steps:
        if name in affected and name not in protected_steps:
            invalidate_step(workflow, name)
            invalidated.append(name)

    return invalidated
