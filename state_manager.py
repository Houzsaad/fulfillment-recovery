from models import Workflow, StepStatus


def mark_running(workflow: Workflow, step_name: str):
    step = workflow.steps[step_name]
    step.status = StepStatus.RUNNING


def mark_completed(workflow: Workflow, step_name: str, output=None):
    step = workflow.steps[step_name]
    step.status = StepStatus.COMPLETED
    step.output = output


def mark_failed(workflow: Workflow, step_name: str):
    step = workflow.steps[step_name]
    step.status = StepStatus.FAILED


def mark_outcome_unknown(workflow: Workflow, step_name: str):
    step = workflow.steps[step_name]
    step.status = StepStatus.OUTCOME_UNKNOWN


def invalidate_step(workflow: Workflow, step_name: str):
    step = workflow.steps[step_name]
    step.status = StepStatus.INVALIDATED
    step.output = None