FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY services/traffic_generator/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy services package root + traffic generator code
COPY services/__init__.py ./services/__init__.py
COPY services/traffic_generator/ ./services/traffic_generator/

# Set Python path
ENV PYTHONPATH=/app

# Run Locust with web UI exposed
CMD ["locust", "-f", "services/traffic_generator/locustfile.py", "--host", "http://load_balancer:8000", "--web-host", "0.0.0.0"]