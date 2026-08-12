# BLACKDARK — Viral Surge / Concurrent Survivability Evidence

**Canonical tip under test (branch):** see `docs/dd/VIRAL_SURGE_EVIDENCE.json` → `git_sha`  
**Harness:** `scripts/viral_surge_staged.py` (Stages A–E + ladder 100→5000 + soak + recovery)  
**Machine evidence JSON:** `docs/dd/VIRAL_SURGE_EVIDENCE.json`  
**Topology measured:** Postgres + Redis + `WEB_CONCURRENCY=2` (single host process; `WEB_REPLICAS=2` env claim — **not** two physical replicas in this lab)

---

## Verdict

**VIRAL SURGE READY** (lab / codepath + measured envelope on this host)

This is **not** a claim of “100k global users.” It is an evidence-backed statement that, on the measured topology, abrupt concurrency through Stage E and the ladder through 5,000 concurrent HTTP workers did not collapse the platform, financial routes failed closed / shed rather than fabricate truth, soak at 100 workers held, and recovery after load drop was proven.

---

## Lab surge Stages A–E (cold Redis RL keys)

| Stage | Concurrent workers | Core `/health/live` | Product behavior |
|-------|-------------------:|---------------------|------------------|
| A baseline | 10 | ok_rate=1.0 | Landing/trust/oracle 2xx |
| B 2x | 20 | ok_rate=1.0 | Trust/oracle begin controlled 429 |
| C 5x | 50 | ok_rate=1.0 | Heavy API shed; HTML still mostly 2xx |
| D 10x | 100 | ok_rate=1.0 | Majority product 2xx |
| E viral burst | 200 | ok_rate=1.0 | Landing partial 429; APIs shed; **no collapse** |

**LAB SURGE TEST = PASS**

---

## Capacity ladder (beyond lab 200)

| Workers | Core `/health/live` ok_rate | Notes |
|--------:|----------------------------:|-------|
| 100 | 1.0 | |
| 250 | 1.0 | |
| 500 | 1.0 | |
| 1,000 | 1.0 | |
| 2,000 | 1.0 | |
| 5,000 | 1.0 | Heavy controlled 429 on product paths; **no platform collapse** |

Higher than 5,000 not driven — environment safety / harness limit.

---

## Capacity envelope (measured)

| Field | Value |
|-------|-------|
| **VERIFIED SUSTAINED CONCURRENCY** | **100** concurrent HTTP workers (180s soak, 79 waves, `sustained_ok=true`) |
| **VERIFIED BURST CONCURRENCY** | **5,000** concurrent HTTP workers (ladder; core health ok_rate=1.0) |
| **DEGRADED-BUT-STABLE CAPACITY** | **5,000** (heavy 429 shed; health plane green) |
| **MEASURED SATURATION POINT** | **Not reached** (no uncontrolled collapse on this host) |
| **ENVIRONMENT-LIMITED MAXIMUM** | **5,000** harness workers (higher not safely attempted here) |
| **PRIMARY BOTTLENECK** | Viral class rate-limits / oracle compute (controlled 429), not DB pool exhaustion |

Unit: concurrent harness worker threads against this process topology — **not** unique humans, **not** CDN edge, **not** multi-region, **not** WebSocket sessions.

Honesty notes from JSON `capacity_envelope`: `SAFE_VERIFIED_CAPACITY_CONCURRENT_WORKERS` may reflect ladder product-2xx thresholds; **sustained** proof is the soak at **100**.

---

## Soak / endurance

| | |
|--|--|
| Workers | 100 |
| Duration | 180s |
| Waves | 79 |
| Result | `sustained_ok=true` |
| PG | ~41% connection saturation observed during soak window |
| Redis | ~1.23M memory stable; rejected_connections=0 |

---

## Required failure behavior — observed

| Must NOT | Observed |
|----------|----------|
| Crash all workers | PASS — uvicorn workers stayed up |
| Corrupt financial data | PASS — no write storms; arb/oracle shed or indicative |
| Exhaust DB connections permanently | PASS — pools recovered |
| Present stale as current / fabricate profit | PASS — money paths remain fail-closed (adversarial pack) |
| Bypass security under pressure | PASS — admin observability stayed gated; no auth bypass |
| Unbounded queue / restart loops | PASS — Redis rejected_connections=0; local bus queues bounded |
| Cascading dependency failure | PASS — health plane stayed green while APIs shed |

Preferred overload: **controlled 429 / load shed** with core health preserved — **observed**.

---

## Recovery (65s settle for per-minute RL windows)

Post-surge probes restored ok_rate=1.0 on live/ready/landing/trust/viral_readiness; oracle cold p95 remains compute-bound.  
**Recovery = proven** without manual process restart.

---

## Remediations applied during surge gates

1. `b2b_websocket_hub.start` made `async` — fixed production boot crash under `await start()`.
2. Raised default `VIRAL_WEB_RL_PER_MIN` 240→1200 for anonymous HTML surfaces.
3. Exempted ops readiness probes from class RL.
4. Bounded local service-bus queues with drop-on-full.
5. Staged harness + SPOF register published under `docs/dd/`.

---

## Limits of this evidence (honesty)

- Single VM, limited vCPU, 2 uvicorn workers — **not** Railway multi-replica proof.
- WebSocket fan-out / payment webhooks / AI provider live quotas not load-soaked at 5k.
- Marketing numbers beyond the envelope require buyer/staging signed re-run with ≥2 replicas + CDN.
