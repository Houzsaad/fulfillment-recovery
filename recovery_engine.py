from models import StepStatus, ResultValidity
from state_manager import (
    mark_completed,
    mark_failed,
    invalidate_step,
)
from dependency_manager import (
    can_execute_step,
    get_downstream_steps,
)

from reservation_service import (
    ReservationStatus,
    ReleaseStatus,
    ReservationReleaseTimeout,
)

def get_idempotency_key(workflow, step_name):
    return f"{workflow.workflow_id}:{step_name}"


def check_reservation_compatibility(workflow, reservation):
    plan_step = workflow.steps["calculate_plan"]

    # The plan must be completed and valid.
    if (
        plan_step.status != StepStatus.COMPLETED
        or plan_step.validity != ResultValidity.VALID
        or plan_step.input_version != workflow.inventory_version
    ):
        return "plan_unavailable"

    plan = plan_step.output

    if not isinstance(plan, dict) or "quantity" not in plan:
        return "plan_unavailable"

    if reservation.quantity == plan["quantity"]:
        return "compatible"

    return "incompatible"


def reconcile_reservation(workflow, step_name, service):
    step = workflow.steps[step_name]

    if step.status != StepStatus.OUTCOME_UNKNOWN:
        raise ValueError("Step does not have an uncertain outcome.")

    key = get_idempotency_key(workflow, step_name)
    reservation = service.get_reservation(key)

    if reservation is None:
        return "not_found"

    if reservation.status == ReservationStatus.CONFIRMED:
        # Preserve whether this reservation belongs to an old version.
        was_stale = step.validity == ResultValidity.STALE

        mark_completed(
            workflow,
            step_name,
            {
                "idempotency_key": key,
                "quantity": reservation.quantity,
                "status": reservation.status.value,
            },
        )

        if was_stale:
            step.validity = ResultValidity.STALE

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

    invalidated = []

    for name in workflow.steps:
        if name in affected:
            invalidate_step(workflow, name)
            invalidated.append(name)

    return invalidated



def reconcile_reservation_release(workflow, step_name, service):
    step = workflow.steps[step_name]

    key = get_idempotency_key(workflow, step_name)
    reservation = service.get_reservation(key)

    if reservation is None:
        return "not_found"

    if reservation.release_status == ReleaseStatus.RELEASED:
        return "released"

    if reservation.release_status == ReleaseStatus.FAILED:
        return "failed"

    if reservation.release_status == ReleaseStatus.PENDING:
        return "pending"

    return "not_started"

def assess_and_compensate_reservation(workflow, service):
    step_name = "reserve_inventory"
    step = workflow.steps[step_name]

    if step.status != StepStatus.COMPLETED:
        return "reservation_unavailable"

    if step.validity != ResultValidity.STALE:
        return "not_stale"

    key = get_idempotency_key(workflow, step_name)
    reservation = service.get_reservation(key)

    if reservation is None:
        return "reservation_not_found"

    compatibility = check_reservation_compatibility(
        workflow, reservation
    )

    if compatibility == "plan_unavailable":
        return "plan_unavailable"

    if compatibility == "compatible":
        step.validity = ResultValidity.VALID
        step.input_version = workflow.inventory_version
        return "compatible"

    try:
        service.release_reservation(key)
    except ReservationReleaseTimeout:
        pass

    release_result = reconcile_reservation_release(
        workflow, step_name, service
    )

    if release_result == "released":
        step.status = StepStatus.PENDING
        step.validity = ResultValidity.UNKNOWN
        return "released_re_reservation_required"

    return f"release_{release_result}"


def recover_workflow(workflow, service, current_inventory_version):
    invalidated = handle_inventory_version_change(
        workflow,
        current_inventory_version,
    )

    reconciliation = {}

    # 1. Reconcile uncertain external operations.
    for name, step in workflow.steps.items():
        if step.status == StepStatus.OUTCOME_UNKNOWN:
            if name == "reserve_inventory":
                reconciliation[name] = reconcile_reservation(
                    workflow, name, service
                )
            else:
                reconciliation[name] = "manual_review"

    # 2. Assess stale reservations and compensate if necessary.
    reservation_step = workflow.steps["reserve_inventory"]

    if (
        reservation_step.status == StepStatus.COMPLETED
        and reservation_step.validity == ResultValidity.STALE
    ):
        reconciliation["reservation_compatibility"] = (
            assess_and_compensate_reservation(workflow, service)
        )

    # 3. Determine which steps are safe to execute.
    ready_steps = []

    for name, step in workflow.steps.items():
        if step.status == StepStatus.OUTCOME_UNKNOWN:
            continue

        if (
            name == "reserve_inventory"
            and step.validity != ResultValidity.VALID
            and step.status != StepStatus.PENDING
        ):
            continue

        if (
            step.status in (
                StepStatus.PENDING,
                StepStatus.INVALIDATED,
            )
            or step.validity == ResultValidity.STALE
        ):
            if can_execute_step(workflow, name):
                ready_steps.append(name)

    unresolved_steps = [
        name
        for name, step in workflow.steps.items()
        if step.status == StepStatus.OUTCOME_UNKNOWN
    ]

    return {
        "invalidated_steps": invalidated,
        "reconciliation": reconciliation,
        "ready_steps": ready_steps,
        "unresolved_steps": unresolved_steps,
    }
