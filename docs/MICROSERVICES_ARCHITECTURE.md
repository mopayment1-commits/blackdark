# BLACKDARK — Microservices Architecture

## Overview

BLACKDARK supports **split deployment** across independent services connected by **Redis pub/sub**.

| Service | Port | Responsibility |
|---------|------|----------------|
| **web** | 8080 | UI, REST API, B2B WebSocket, billing |
| **aggregator** | 8091 | Market polling, exchange WS, hot storage |
| **arbitrage** | 8092 | Scan, alerts, auto-execution, low latency |
| **ingestion** | 8093 | News, macro, data lake scheduler |
| **all** | 8080 | Monolith (legacy / dev) |

## Quick Start

### Monolith (development)
```bash
python run_service.py all
# or
uvicorn dashboard:app --port 8080
```

### Microservices (production scale)
```bash
docker compose up -d
docker compose up -d --scale web=3 --scale arbitrage=2
```

### Single service manually
```bash
python run_service.py web
python run_service.py aggregator
python run_service.py arbitrage
python run_service.py ingestion
```

## Environment

```env
SERVICE_MODE=web          # web | aggregator | arbitrage | ingestion | all
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://user:pass@host:5432/blackdark  # production (SQLite if empty)
HEALTH_PORT=8180          # instant liveness sidecar (default: app port + 100)
SERVICE_BUS_LOCAL=true    # in-process fallback when Redis absent
```

## Service Bus Channels

| Channel | Publisher | Subscriber | Payload |
|---------|-----------|------------|---------|
| `blackdark.market.updated` | aggregator | arbitrage, web | cycle complete |
| `blackdark.arbitrage.hot` | arbitrage | web, analytics | hot opportunity |

## Health Checks

```
GET :8180/health/live        — sidecar liveness (<10ms, Docker/K8s)
GET /health/live             — app liveness (may wait if event loop busy)
GET /health/ready            — DB + Redis readiness
GET /api/services/status     — architecture + bus stats
python scripts/verify_buyer.py http://127.0.0.1:8080
```

## Scaling Path (1K → 1M users)

1. **Today:** `docker compose --scale web=N --scale arbitrage=M`
2. **Redis:** shared cache + pub/sub between replicas
3. **PostgreSQL:** replace SQLite for concurrent writes (DATABASE_URL)
4. **Railway/K8s:** HPA on CPU + request rate per service
5. **CDN:** static assets off main web tier

## Files

```
run_service.py              — launcher CLI
microservices/
  lifecycle.py              — boot/shutdown per mode
  worker_app.py               — worker health HTTP
service_bus.py              — Redis pub/sub
docker-compose.yml          — full stack
```
