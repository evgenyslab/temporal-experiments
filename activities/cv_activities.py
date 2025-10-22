from temporalio import activity
import asyncio
import random
import logging


logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


@activity.defn
async def process_file(file_path: str, dataset_info: dict) -> None:
    """Simulate computer vision processing on a file"""
    activity.logger.info(f"Processing file: {file_path}")
    logger.info(f"Processing file: {file_path}")
    
    # Simulate heavy CV processing (10-30 seconds)
    processing_time = random.uniform(45, 60)
    await asyncio.sleep(processing_time)
    
    # Mock CV results
    result = {
        'file': file_path,
        'dataset_id': dataset_info['dataset_id'],
        'processing_time': processing_time,
        'objects_detected': random.randint(1, 10),
        'features': [random.random() for _ in range(128)],  # Feature vector
        'confidence': random.uniform(0.7, 0.99)
    }
    
    activity.logger.info(f"Completed processing {file_path} in {processing_time:.2f}s")
    return None
