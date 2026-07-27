FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared module
COPY shared/ ./shared/

# Copy service code
COPY services/ml_service/ ./services/ml_service/

# Set Python path
ENV PYTHONPATH=/app

# Run the service
CMD ["uvicorn", "services.ml_service.main:app", "--host", "0.0.0.0", "--port", "8100"]