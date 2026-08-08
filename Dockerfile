FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    HOST=0.0.0.0 \
    SERVICE_MODE=web \
    RUN_AGGREGATOR=false \
    MANIFEST_AUTO_APPROVE=true \
    MANIFEST_REQUIRE_REVIEW=false

# Minimal OS deps for wheels; keep image lean for Railway trial builds
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app \
    && useradd --system --gid app --create-home --home-dir /home/app app

COPY requirements-prod.txt requirements.txt
# --only-binary :all: avoids executing untrusted setup scripts from sdists (Sonar S8541).
RUN pip install --no-cache-dir --default-timeout=180 --upgrade "pip==25.2" \
    && pip install --no-cache-dir --default-timeout=180 --only-binary=:all: -r requirements.txt

COPY *.py ./
COPY api/ api/
COPY repos/ repos/
COPY bd_platform/ bd_platform/
COPY ml/ ml/
COPY microservices/ microservices/
COPY templates/ templates/
COPY static/ static/
COPY data/operational_manifest.json data/
COPY data/models/ data/models/
COPY BUILD.txt ./
RUN mkdir -p data/models && chown -R app:app /app

USER app

EXPOSE 8080

HEALTHCHECK --interval=5s --timeout=2s --start-period=20s --retries=3 \
    CMD python -c "import os,urllib.request; p=os.getenv('PORT','8080'); urllib.request.urlopen(f'http://127.0.0.1:{p}/health/live', timeout=2)"

CMD ["sh", "-c", "exec python run_service.py ${SERVICE_MODE:-web} --port ${PORT:-8080}"]
