from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    OUTCOME_UNKNOWN = "outcome_unknown"
    INVALIDATED = "invalidated"

@dataclass
class WorkflowStep:
    name: str
    status: StepStatus = StepStatus.PENDING
    dependencies: list[str] = field(default_factory=list)
    input_version: int | None = None
    output: Any = None


@dataclass
class Workflow:
    workflow_id: str
    inventory_version: int
    steps: dict[str, WorkflowStep] = field(default_factory=dict)