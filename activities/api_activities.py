from temporalio import activity
import asyncio


@activity.defn
async def get_dataset_info(dataset_id: int) -> dict:
    """Simulate API call to get dataset metadata"""
    activity.logger.info(f"Fetching dataset info for ID: {dataset_id}")
    
    # Simulate API call
    await asyncio.sleep(1)
    
    # Mock response
    return {
        'dataset_id': dataset_id,
        'name': f'Dataset {dataset_id}',
        's3_bucket': 'my-datasets',
        's3_prefix': f'dataset-{dataset_id}/',
        'description': 'Sample dataset for processing'
    }
