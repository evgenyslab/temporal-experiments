"""
Script to trigger a workflow from outside the cluster.
Usage: python trigger_workflow.py <dataset_id>
"""
import asyncio
import sys
from temporalio.client import Client
from workflows.dataset_workflow import DatasetProcessingWorkflow


async def main():
    dataset_id = int(sys.argv[1]) if len(sys.argv) > 1 else 123
    
    print(f"Connecting to Temporal...")
    client = await Client.connect("localhost:7233")
    
    print(f"Starting workflow for dataset {dataset_id}...")
    result = await client.execute_workflow(
        DatasetProcessingWorkflow.run,
        args=[dataset_id],
        id=f"dataset-{dataset_id}",
        task_queue="workflow-queue",
    )
    
    print(f"\nWorkflow completed!")
    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
