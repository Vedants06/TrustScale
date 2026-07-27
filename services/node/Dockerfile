FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY services/node/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared code
COPY shared/ ./shared/

# Copy services package root + node code
COPY services/__init__.py ./services/__init__.py
COPY services/node/ ./services/node/

# Set Python path
ENV PYTHONPATH=/app

# Run service
CMD ["uvicorn", "services.node.main:app", "--host", "0.0.0.0", "--port", "8001"]