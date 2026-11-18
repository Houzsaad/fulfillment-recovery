from models import StepStatus
from reservation_service import ReservationStatus
from state_manager import mark_completed, mark_failed


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