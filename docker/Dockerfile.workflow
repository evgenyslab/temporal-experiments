FROM python:3.12-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir temporalio

# Copy application code
COPY workflows/ ./workflows/
COPY activities/ ./activities/
COPY workers/workflow_worker.py ./
COPY scripts/ ./scripts/

# Use unbuffered Python output
ENV PYTHONUNBUFFERED=1

CMD ["python", "-u", "workflow_worker.py"]
