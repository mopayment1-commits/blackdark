FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    SERVICE_MODE=web \
    RUN_AGGREGATOR=false \
    MANIFEST_AUTO_APPROVE=true \
    MANIFEST_REQUIRE_REVIEW=false

# Minimal OS deps for wheels; keep image lean for Railway trial builds.
# hadolint ignore=DL3008 -- ca-certificates follows Debian security updates
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser

# Hash-locked + wheels-only (Sonar docker:S8541 / S8544).
COPY requirements-prod.hashes.txt requirements.txt
RUN pip install --no-cache-dir --default-timeout=180 --require-hashes --only-binary=:all: -r requirements.txt

# CAP646/CAP978 API packages (see COPY cap646 cap978 rvm docs/cap646 docs/cap978)
COPY *.py ./
COPY api/ api/
COPY cap646/ cap646/
COPY cap978/ cap978/
COPY rvm/ rvm/
COPY repos/ repos/
COPY bd_platform/ bd_platform/
COPY ml/ ml/
COPY microservices/ microservices/
COPY dbt_blackdark/ dbt_blackdark/
COPY templates/ templates/
COPY static/ static/
RUN mkdir -p data/models
COPY data/operational_manifest.json data/
COPY data/institutional_assurance/signed_capacity.json data/institutional_assurance/
COPY docs/LOAD_TEST_RUN_LOG.md docs/
COPY docs/cap646/ docs/cap646/
COPY docs/cap978/ docs/cap978/
COPY docs/evidence/signed_load_production_cap644.json docs/evidence/
COPY railway.json ./
# Bake trained model artifacts when present (ignore if empty in some CI contexts)
COPY data/models/ data/models/
COPY BUILD.txt ./

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

HEALTHCHECK --interval=5s --timeout=2s --start-period=20s --retries=3 \
    CMD python -c "import os,urllib.request; p=os.getenv('PORT','8080'); urllib.request.urlopen(f'http://127.0.0.1:{p}/health/live', timeout=2)"

CMD ["sh", "-c", "exec python run_service.py ${SERVICE_MODE:-web} --port ${PORT:-8080}"]
