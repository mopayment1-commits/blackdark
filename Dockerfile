FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    RUN_AGGREGATOR=true \
    MANIFEST_AUTO_APPROVE=true \
    MANIFEST_REQUIRE_REVIEW=false

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=120 -r requirements.txt

COPY *.py ./
COPY templates/ templates/
COPY static/ static/
RUN mkdir -p data
COPY data/operational_manifest.json data/

EXPOSE 8080

CMD ["sh", "-c", "exec uvicorn dashboard:app --host 0.0.0.0 --port ${PORT:-8080}"]
