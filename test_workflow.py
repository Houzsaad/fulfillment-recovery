from workflow import create_workflow

workflow = create_workflow("order-001", 17)

for name, step in workflow.steps.items():
    print(name, step.status.value, step.dependencies)