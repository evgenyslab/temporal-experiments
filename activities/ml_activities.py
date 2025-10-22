from temporalio import activity
import asyncio
import random


@activity.defn
async def analyze_cv_results(cv_result: dict, dataset_info: dict) -> None:
    """Simulate ML analysis on CV results"""
    activity.logger.info(f"Analyzing CV results for file: {cv_result['file']}")
    
    # Simulate ML inference (5-15 seconds)
    inference_time = random.uniform(5, 15)
    await asyncio.sleep(inference_time)
    
    # Mock ML predictions
    categories = ['cat', 'dog', 'bird', 'car', 'person']
    result = {
        'file': cv_result['file'],
        'dataset_id': dataset_info['dataset_id'],
        'cv_confidence': cv_result['confidence'],
        'predicted_class': random.choice(categories),
        'ml_confidence': random.uniform(0.8, 0.99),
        'inference_time': inference_time,
        'model_version': 'v1.2.3'
    }
    
    activity.logger.info(f"Completed analysis for {cv_result['file']} in {inference_time:.2f}s")
    return None
