import asyncio
import os
from temporalio.client import Client
from temporalio.worker import Worker
from workflows.dataset_workflow import DatasetProcessingWorkflow


async def main():
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    print(f"Connecting to Temporal at {temporal_address}")
    
    client = await Client.connect(temporal_address)
    
    worker = Worker(
        client,
        task_queue="workflow-queue",
        workflows=[DatasetProcessingWorkflow],
        activities=[],  # No activities on workflow worker
    )
    
    print("Workflow worker started, listening on 'workflow-queue'")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
