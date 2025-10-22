#!/usr/bin/env python3
"""
Trigger a workflow from your local machine.

This script triggers workflows by name (workflow type string), not by importing
the workflow class. This is how an API would typically trigger workflows.

Prerequisites:
1. Port-forward Temporal frontend: kubectl port-forward -n temporal-demo svc/temporal-frontend 7233:7233
2. Port-forward Temporal UI: kubectl port-forward -n temporal-demo svc/temporal-ui 8080:8080
"""
import asyncio
from temporalio.client import Client


async def main():
    # Connect to Temporal via port-forward
    client = await Client.connect("localhost:7233")

    dataset_id = 123
    workflow_id = f"dataset-{dataset_id}"

    print(f"Starting workflow for dataset {dataset_id}")
    print(f"Workflow ID: {workflow_id}")

    # Start the workflow by name (workflow type string)
    # This is how an API would trigger workflows - no need to import the workflow class
    handle = await client.start_workflow(
        "DatasetProcessingWorkflow",  # Workflow type name as string
        args=[dataset_id],
        id=workflow_id,
        task_queue="workflow-queue",
    )

    print(f"✓ Workflow started successfully!")
    print(f"  Run ID: {handle.result_run_id}")
    print(f"\nView it at: http://localhost:8080/namespaces/default/workflows/{workflow_id}")
    print(f"\nWorkflow is running. You can now:")
    print(f"1. Open Temporal UI: http://localhost:8080")
    print(f"2. Navigate to Workflows tab")
    print(f"3. Search for workflow ID: {workflow_id}")

    # Wait for result (optional - can comment out to just start it)
    # result = await handle.result()
    # print(f"Workflow completed with result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
