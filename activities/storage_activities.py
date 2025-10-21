from temporalio import activity
import asyncio


@activity.defn
async def list_dataset_files(bucket: str, prefix: str) -> list[str]:
    """Simulate listing files from S3"""
    activity.logger.info(f"Listing files from s3://{bucket}/{prefix}")
    
    # Simulate S3 API call
    await asyncio.sleep(0.5)
    
    # Mock file list - return 20 files to trigger scaling
    file_count = 20
    files = [f"{prefix}image_{i:04d}.jpg" for i in range(file_count)]
    
    activity.logger.info(f"Found {len(files)} files")
    return files
