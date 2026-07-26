FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agents/ ./agents/
COPY runbooks/ ./runbooks/

ENV PYTHONPATH=/app
ENV OTEL_SERVICE_NAME=sre-copilot
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

EXPOSE 8080

CMD ["python", "agents/orchestrator.py"]
