FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir temporalio

# Copy application code
COPY workflows/ ./workflows/
COPY activities/ ./activities/
COPY workers/workflow_worker.py ./

CMD ["python", "workflow_worker.py"]
