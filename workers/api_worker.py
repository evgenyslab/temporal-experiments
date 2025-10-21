import asyncio
import os
from temporalio.client import Client
from temporalio.worker import Worker
from activities.api_activities import get_dataset_info
from activities.storage_activities import list_dataset_files


async def main():
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    print(f"Connecting to Temporal at {temporal_address}")
    
    client = await Client.connect(temporal_address)
    
    worker = Worker(
        client,
        task_queue="api-workers",
        workflows=[],
        activities=[get_dataset_info, list_dataset_files],
    )
    
    print("API worker started, listening on 'api-workers' queue")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
