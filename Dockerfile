FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
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
COPY templates/ templates/
COPY static/ static/
RUN mkdir -p data
COPY data/operational_manifest.json data/
COPY BUILD.txt ./

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health')"

CMD ["sh", "-c", "exec uvicorn dashboard:app --host 0.0.0.0 --port ${PORT:-8080}"]
