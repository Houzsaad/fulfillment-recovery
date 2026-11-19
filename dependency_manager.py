from models import Workflow

from state_manager import invalidate_step

from models import Workflow, StepStatus

def get_downstream_steps(workflow: Workflow, step_name: str) -> list[str]:
    affected = []
    visited = set()
    queue = [step_name]

    while queue:
        current = queue.pop(0)

        if current in visited:
            continue

        visited.add(current)

        for name, step in workflow.steps.items():
            if current in step.dependencies and name not in visited:
                affected.append(name)
                queue.append(name)

    return affected

def invalidate_downstream_steps(workflow, step_name):
    affected = get_downstream_steps(workflow, step_name)

    for name in affected:
        invalidate_step(workflow, name)

    return affected

def can_execute_step(workflow, step_name):
    step = workflow.steps[step_name]

    for dependency_name in step.dependencies:
        dependency = workflow.steps[dependency_name]

        if dependency.status != StepStatus.COMPLETED:
            return False

        if not can_execute_step(workflow, dependency_name):
            return False

    return True