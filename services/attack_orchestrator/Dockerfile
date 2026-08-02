FROM python:3.13-slim

WORKDIR /app

COPY services/attack_orchestrator/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY services/__init__.py ./services/__init__.py
COPY services/attack_orchestrator/ ./services/attack_orchestrator/
COPY config/ ./config/
COPY research/data/experiments/ ./research/data/experiments/

ENV PYTHONPATH=/app

CMD ["uvicorn", "services.attack_orchestrator.main:app", "--host", "0.0.0.0", "--port", "8200"]