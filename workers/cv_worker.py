import asyncio
import os
from temporalio.client import Client
from temporalio.worker import Worker
from activities.cv_activities import process_file


async def main():
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    print(f"Connecting to Temporal at {temporal_address}")
    
    client = await Client.connect(temporal_address)
    
    worker = Worker(
        client,
        task_queue="cv-workers",
        workflows=[],
        activities=[process_file],
    )
    
    print("CV worker started, listening on 'cv-workers' queue")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
