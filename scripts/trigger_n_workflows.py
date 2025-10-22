#!/usr/bin/env python3
"""
Script to trigger N workflows with numbered input arguments.
This script can be run from inside the Kubernetes cluster.

Usage: python trigger_n_workflows.py <num_workflows> [start_id] [workflow_count_arg]

Examples:
  python trigger_n_workflows.py 10              # Triggers 10 workflows with IDs 1-10
  python trigger_n_workflows.py 5 100           # Triggers 5 workflows with IDs 100-104
  python trigger_n_workflows.py 5 100 1000      # Triggers 5 workflows with IDs 100-104,
                                                 # each workflow gets 1000 as input arg
"""
import asyncio
import sys
import os
from temporalio.client import Client


async def trigger_workflow(client: Client, dataset_id: int, workflow_count_arg: int = None):
    """Trigger a single workflow for the given dataset ID."""
    workflow_id = f"dataset-{dataset_id}"

    # Build workflow arguments based on whether count argument is provided
    if workflow_count_arg is not None:
        workflow_args = [dataset_id, workflow_count_arg]
        arg_display = f"args=[{dataset_id}, {workflow_count_arg}]"
    else:
        workflow_args = [dataset_id]
        arg_display = f"args=[{dataset_id}]"

    try:
        handle = await client.start_workflow(
            "DatasetProcessingWorkflow",  # Workflow type name as string
            args=workflow_args,
            id=workflow_id,
            task_queue="workflow-queue",
        )
        print(f"✓ Workflow {dataset_id} started: {workflow_id} {arg_display} (Run ID: {handle.result_run_id[:8]}...)")
        return True
    except Exception as e:
        print(f"✗ Workflow {dataset_id} failed: {e}")
        return False


async def main():
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python trigger_n_workflows.py <num_workflows> [start_id] [workflow_count_arg]")
        print("  num_workflows      - Number of workflows to trigger")
        print("  start_id           - Starting dataset ID (default: 1)")
        print("  workflow_count_arg - Additional count argument to pass to each workflow (optional)")
        sys.exit(1)

    num_workflows = int(sys.argv[1])
    start_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    workflow_count_arg = int(sys.argv[3]) if len(sys.argv) > 3 else None

    # Connect to Temporal (using internal service name)
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "temporal-frontend.temporal-demo.svc.cluster.local:7233")
    print(f"Connecting to Temporal at {temporal_address}")

    client = await Client.connect(temporal_address)

    # Display what we're doing
    if workflow_count_arg is not None:
        print(f"\nTriggering {num_workflows} workflows (IDs {start_id} to {start_id + num_workflows - 1})")
        print(f"Each workflow will receive count argument: {workflow_count_arg}")
    else:
        print(f"\nTriggering {num_workflows} workflows (IDs {start_id} to {start_id + num_workflows - 1})")
    print("-" * 70)

    # Trigger workflows concurrently
    tasks = []
    for i in range(num_workflows):
        dataset_id = start_id + i
        tasks.append(trigger_workflow(client, dataset_id, workflow_count_arg))

    # Wait for all workflows to start
    results = await asyncio.gather(*tasks)

    # Summary
    print("-" * 70)
    success_count = sum(results)
    print(f"\nSummary: {success_count}/{num_workflows} workflows started successfully")

    if success_count > 0:
        print(f"\nView in Temporal UI:")
        print(f"  kubectl port-forward -n temporal-demo svc/temporal-ui 8080:8080")
        print(f"  Then open: http://localhost:8080/namespaces/default/workflows")

    # Exit with error if any workflow failed
    if success_count < num_workflows:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
