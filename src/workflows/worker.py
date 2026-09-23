import asyncio
import os
import logging
from temporalio.client import Client
from temporalio.worker import Worker
from src.workflows.verify_workflow import VerifyReportWorkflow
from src.workflows.activities import (
    parse_input_activity,
    extract_claims_activity,
    link_edgar_source_activity,
    symbolic_reexecute_activity,
    sign_certificate_activity,
    aggregate_report_activity,
    execute_webhook_activity
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def connect_with_retry(host: str, port: str, max_retries: int = 30, delay: int = 2) -> Client:
    """Connect to Temporal server with retry logic."""
    target = f"{host}:{port}"
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Attempting to connect to Temporal at {target} (attempt {attempt}/{max_retries})...")
            client = await Client.connect(target)
            logger.info(f"Successfully connected to Temporal server at {target}")
            return client
        except Exception as e:
            logger.warning(f"Temporal not ready yet ({e}). Retrying in {delay}s...")
            await asyncio.sleep(delay)
    raise RuntimeError(f"Could not connect to Temporal at {target} after {max_retries} attempts.")

async def main():
    temporal_host = os.getenv("TEMPORAL_HOST", "temporal")
    temporal_port = os.getenv("TEMPORAL_PORT", "7233")
    task_queue = os.getenv("FINVERIFY_TASK_QUEUE", "finverify-task-queue")
    
    client = await connect_with_retry(temporal_host, temporal_port)
    
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[VerifyReportWorkflow],
        activities=[
            parse_input_activity,
            extract_claims_activity,
            link_edgar_source_activity,
            symbolic_reexecute_activity,
            sign_certificate_activity,
            aggregate_report_activity,
            execute_webhook_activity
        ]
    )
    
    logger.info(f"Starting Temporal worker on queue {task_queue}")
    await worker.run()

if __name__ == '__main__':
    asyncio.run(main())
