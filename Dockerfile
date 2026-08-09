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
# hadolint ignore=DL3008
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    # hadolint: ca-certificates tracks Debian security updates; pin optional
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser

# Locked == pins + wheels-only (Sonar docker:S8541 / S8544).
COPY requirements-prod.lock.txt requirements.txt
RUN pip install --no-cache-dir --default-timeout=180 --only-binary=:all: -r requirements.txt

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

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

HEALTHCHECK --interval=5s --timeout=2s --start-period=20s --retries=3 \
    CMD python -c "import os,urllib.request; p=os.getenv('PORT','8080'); urllib.request.urlopen(f'http://127.0.0.1:{p}/health/live', timeout=2)"

CMD ["sh", "-c", "exec python run_service.py ${SERVICE_MODE:-web} --port ${PORT:-8080}"]
