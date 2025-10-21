from temporalio import workflow
from datetime import timedelta
import asyncio

with workflow.unsafe.imports_passed_through():
    from activities.api_activities import get_dataset_info
    from activities.storage_activities import list_dataset_files
    from activities.cv_activities import process_file
    from activities.ml_activities import analyze_cv_results


@workflow.defn
class DatasetProcessingWorkflow:
    @workflow.run
    async def run(self, dataset_id: int):
        workflow.logger.info(f"Starting workflow for dataset {dataset_id}")
        
        # Task 1: Get dataset metadata from API
        dataset_info = await workflow.execute_activity(
            get_dataset_info,
            args=[dataset_id],
            schedule_to_close_timeout=timedelta(minutes=5),
            task_queue="api-workers"
        )
        workflow.logger.info(f"Got dataset info: {dataset_info}")
        
        # Task 2: List files in S3
        file_paths = await workflow.execute_activity(
            list_dataset_files,
            args=[dataset_info['s3_bucket'], dataset_info['s3_prefix']],
            schedule_to_close_timeout=timedelta(minutes=5),
            task_queue="api-workers"
        )
        workflow.logger.info(f"Found {len(file_paths)} files to process")
        
        # Task 3: Fan-out to process each file in parallel (CV workers)
        cv_tasks = [
            workflow.execute_activity(
                process_file,
                args=[file_path, dataset_info],
                schedule_to_close_timeout=timedelta(minutes=30),
                task_queue="cv-workers"
            )
            for file_path in file_paths
        ]
        
        workflow.logger.info(f"Starting {len(cv_tasks)} CV processing tasks")
        cv_results = await asyncio.gather(*cv_tasks)
        workflow.logger.info(f"Completed {len(cv_results)} CV processing tasks")
        
        # Task 4: Fan-out ML analysis for each CV result (ML workers)
        ml_tasks = [
            workflow.execute_activity(
                analyze_cv_results,
                args=[cv_result, dataset_info],
                schedule_to_close_timeout=timedelta(hours=1),
                task_queue="ml-workers"
            )
            for cv_result in cv_results
        ]
        
        workflow.logger.info(f"Starting {len(ml_tasks)} ML analysis tasks")
        ml_results = await asyncio.gather(*ml_tasks)
        workflow.logger.info(f"Completed {len(ml_results)} ML analysis tasks")
        
        return {
            'dataset_id': dataset_id,
            'files_processed': len(cv_results),
            'cv_results': cv_results,
            'ml_results': ml_results
        }
