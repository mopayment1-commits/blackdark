FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    SERVICE_MODE=web \
    RUN_AGGREGATOR=false \
    MANIFEST_AUTO_APPROVE=true \
    MANIFEST_REQUIRE_REVIEW=false

# Minimal OS deps for wheels; keep image lean for Railway trial builds
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-prod.txt requirements.txt
RUN pip install --no-cache-dir --default-timeout=180 -r requirements.txt

COPY *.py ./
COPY api/ api/
COPY repos/ repos/
COPY bd_platform/ bd_platform/
COPY ml/ ml/
COPY microservices/ microservices/
COPY templates/ templates/
COPY static/ static/
RUN mkdir -p data/models
COPY data/operational_manifest.json data/
# Bake trained model artifacts when present (ignore if empty in some CI contexts)
COPY data/models/ data/models/
COPY BUILD.txt ./

EXPOSE 8080

HEALTHCHECK --interval=5s --timeout=2s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8180/health/live', timeout=2)"

CMD ["sh", "-c", "exec python run_service.py ${SERVICE_MODE:-web} --port ${PORT:-8080}"]
