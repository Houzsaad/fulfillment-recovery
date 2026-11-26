from models import Workflow, StepStatus, ResultValidity


def mark_running(workflow: Workflow, step_name: str):
    step = workflow.steps[step_name]
    step.status = StepStatus.RUNNING
    step.validity = ResultValidity.UNKNOWN


def mark_completed(workflow: Workflow, step_name: str, output=None):
    step = workflow.steps[step_name]
    step.status = StepStatus.COMPLETED
    step.validity = ResultValidity.VALID
    step.output = output


def mark_failed(workflow: Workflow, step_name: str):
    step = workflow.steps[step_name]
    step.status = StepStatus.FAILED


def mark_outcome_unknown(workflow: Workflow, step_name: str):
    step = workflow.steps[step_name]
    step.status = StepStatus.OUTCOME_UNKNOWN
    step.validity = ResultValidity.UNKNOWN


def invalidate_step(workflow: Workflow, step_name: str):
    step = workflow.steps[step_name]
    step.validity = ResultValidity.STALE