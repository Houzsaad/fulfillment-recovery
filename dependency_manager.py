from models import Workflow


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