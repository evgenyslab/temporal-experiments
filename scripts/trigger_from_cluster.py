#!/usr/bin/env python3
"""
Script to trigger a workflow from inside the Kubernetes cluster.
This is used by the Makefile's trigger-workflow target.

This script triggers workflows by name (workflow type), not by importing
the workflow class. This is how an API would typically trigger workflows.
"""
import asyncio
import sys
import os
from temporalio.client import Client


async def main():
    # Get dataset ID from command line or environment
    if len(sys.argv) > 1:
        dataset_id = int(sys.argv[1])
    else:
        dataset_id = int(os.getenv("DATASET_ID", "123"))

    # Connect to Temporal (using internal service name)
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "temporal-frontend.temporal-demo.svc.cluster.local:7233")
    print(f"Connecting to Temporal at {temporal_address}")

    client = await Client.connect(temporal_address)

    workflow_id = f"dataset-{dataset_id}"
    print(f"Starting workflow for dataset {dataset_id}")
    print(f"Workflow ID: {workflow_id}")

    # Start the workflow by name (workflow type string)
    # This is how an API would trigger workflows - no need to import the workflow class
    try:
        handle = await client.start_workflow(
            "DatasetProcessingWorkflow",  # Workflow type name as string
            args=[dataset_id],
            id=workflow_id,
            task_queue="workflow-queue",
        )
        print(f"✓ Workflow started successfully!")
        print(f"  Workflow ID: {workflow_id}")
        print(f"  Run ID: {handle.result_run_id}")
        print(f"\nView in Temporal UI:")
        print(f"  kubectl port-forward -n temporal-demo svc/temporal-ui 8080:8080")
        print(f"  Then open: http://localhost:8080/namespaces/default/workflows/{workflow_id}")
    except Exception as e:
        print(f"✗ Failed to start workflow: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
