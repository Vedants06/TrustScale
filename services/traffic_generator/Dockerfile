FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY services/traffic_generator/ ./services/traffic_generator/

# Set working directory for locust
WORKDIR /app/services/traffic_generator

# Run locust
CMD ["locust", "-f", "locustfile.py"]