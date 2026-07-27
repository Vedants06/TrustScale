FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared module
COPY shared/ ./shared/

# Copy service code
COPY services/node/ ./services/node/

# Set Python path
ENV PYTHONPATH=/app

# Run the service
CMD ["uvicorn", "services.node.main:app", "--host", "0.0.0.0", "--port", "8001"]