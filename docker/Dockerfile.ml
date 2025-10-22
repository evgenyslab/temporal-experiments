FROM python:3.12

WORKDIR /app

# Install ML dependencies (simulated - add real ones in production)
RUN pip install --no-cache-dir temporalio

# In production, you'd add:
# RUN pip install tensorflow scikit-learn numpy pandas

# Copy application code
COPY activities/ml_activities.py ./activities/
COPY activities/__init__.py ./activities/
COPY workers/ml_worker.py ./

# Use unbuffered Python output
ENV PYTHONUNBUFFERED=1

CMD ["python", "-u", "ml_worker.py"]
