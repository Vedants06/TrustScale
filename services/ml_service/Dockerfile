FROM python:3.13-slim

WORKDIR /app

# Install dependencies with extra timeout for large packages like torch
COPY services/ml_service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --timeout 600 \
    --index-url https://download.pytorch.org/whl/cpu \
    --extra-index-url https://pypi.org/simple \
    torch && \
    pip install --no-cache-dir --timeout 600 -r requirements.txt

# Copy shared package
COPY shared/ ./shared/

# Copy services package root + ml service code
COPY services/__init__.py ./services/__init__.py
COPY services/ml_service/ ./services/ml_service/

# Copy trained model if it exists
COPY research/data/models/ ./research/data/models/

# Set Python path
ENV PYTHONPATH=/app

# Run service
CMD ["uvicorn", "services.ml_service.main:app", "--host", "0.0.0.0", "--port", "8100"]