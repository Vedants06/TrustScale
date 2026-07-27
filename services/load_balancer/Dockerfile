FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY services/load_balancer/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared code
COPY shared/ ./shared/

# Copy services package root + load balancer code
COPY services/__init__.py ./services/__init__.py
COPY services/load_balancer/ ./services/load_balancer/

# Set Python path
ENV PYTHONPATH=/app

# Run service
CMD ["uvicorn", "services.load_balancer.main:app", "--host", "0.0.0.0", "--port", "8000"]