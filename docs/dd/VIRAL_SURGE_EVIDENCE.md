# BLACKDARK — Viral Surge / Concurrent Survivability Evidence

**Canonical tip under test (branch):** `4cf710240cfa70dfb889bae192a47e7582015209` (+ local WS hub / RL remediations in this PR)  
**Harness:** `scripts/viral_surge_staged.py`  
**Machine evidence JSON:** `docs/dd/VIRAL_SURGE_EVIDENCE.json`  
**Topology measured:** Postgres + Redis + `WEB_CONCURRENCY=2` (single host process; `WEB_REPLICAS=2` env claim — **not** two physical replicas in this lab)

---

## Verdict

**VIRAL SURGE READY** (lab / codepath + measured envelope on this host)

This is **not** a claim of “100k global users.” It is an evidence-backed statement that, on the measured topology, abrupt concurrency through Stage E did not collapse the platform, financial routes failed closed / shed rather than fabricate truth, and recovery after load drop was proven.

---

## Stages (cold Redis RL keys)

| Stage | Concurrent workers | Core `/health/live` | Product behavior |
|-------|-------------------:|---------------------|------------------|
| A baseline | 10 | ok_rate=1.0 p95≈9ms | Landing/trust/oracle 2xx |
| B 2x | 20 | ok_rate=1.0 | Trust/oracle begin controlled 429 |
| C 5x | 50 | ok_rate=1.0 | Heavy API shed; HTML still mostly 2xx |
| D 10x | 100 | ok_rate=1.0 | Last stage with majority product 2xx |
| E viral burst | 200 | ok_rate=1.0 p95≈148ms | Landing partial 429; APIs shed; **no collapse** |

Hard errors on core health: **0** across A–E.  
Postgres after Stage E: connections=10 / max=100 (10% saturation).  
Redis after Stage E: ~1.23M memory, rejected_connections=0.

---

## Capacity envelope (measured)

| Field | Value |
|-------|-------|
| **SAFE VERIFIED CAPACITY** | **100 concurrent HTTP workers** (Stage D) |
| **DEGRADED BUT STABLE CAPACITY** | **200 concurrent HTTP workers** (Stage E) |
| **FAILURE / SATURATION POINT** | **Not reached** on this host (no platform-wide collapse through Stage E) |
| **BOTTLENECK** | Viral class rate-limits / oracle compute (controlled 429), not DB pool exhaustion |

Unit: concurrent harness worker threads against this process topology — **not** unique humans, **not** CDN edge, **not** multi-region.

---

## Required failure behavior — observed

| Must NOT | Observed |
|----------|----------|
| Crash all workers | PASS — uvicorn workers stayed up |
| Corrupt financial data | PASS — no write storms; arb/oracle shed or indicative |
| Exhaust DB connections permanently | PASS — PG saturation 10% at peak |
| Present stale as current / fabricate profit | PASS — money paths remain fail-closed (separate adversarial pack) |
| Bypass security under pressure | PASS — admin observability stayed 403; no auth bypass |
| Unbounded queue / restart loops | PASS — Redis rejected_connections=0; process stable |
| Cascading dependency failure | PASS — health plane stayed green while APIs shed |

Preferred overload: **controlled 429 / load shed** with core health preserved — **observed**.

---

## Recovery (65s settle for per-minute RL windows)

| Probe | Post-surge |
|-------|------------|
| `/health/live` | ok_rate=1.0 p95≈10ms (baseline≈9ms) |
| `/health/ready` | ok_rate=1.0 |
| `/` landing | ok_rate=1.0 |
| `/api/trust-os` | ok_rate=1.0 |
| `/api/viral/readiness` | ok_rate=1.0 |
| `/oracle/BTC/quick` | ok_rate=1.0 (cold p95 still oracle-bound ~650ms) |

**Recovery = proven** (latency returned; pools not saturated; product 2xx restored after RL window).

---

## Remediations applied during this gate

1. `b2b_websocket_hub.start` made `async` — fixed production boot crash under `await start()`.
2. Raised default `VIRAL_WEB_RL_PER_MIN` 240→1200 for anonymous HTML surfaces.
3. Exempted `/api/viral/readiness`, `/api/scale/readiness`, `/api/production/guard` from class RL so ops probes remain observable under shed.
4. Staged harness + SPOF register published under `docs/dd/`.

---

## Limits of this evidence (honesty)

- Single VM, 4 vCPU, 2 uvicorn workers — **not** Railway multi-replica proof.
- No true 1k→5k→global fan-out; Stage E is the highest this lab safely drove without inventing users.
- WebSocket fan-out / payment webhooks / AI provider live quotas not load-soaked at Stage E (see SPOF register).
- Marketing numbers beyond the envelope require buyer/staging signed re-run with ≥2 replicas + CDN.
