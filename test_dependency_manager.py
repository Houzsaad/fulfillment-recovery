from workflow import create_workflow
from dependency_manager import get_downstream_steps

workflow = create_workflow("order-001", 17)

affected = get_downstream_steps(workflow, "calculate_plan")

print(affected)