# 04 — Architecture & Reachability (Wave 2)

**Generated:** 2026-09-10T23:50:00Z | **Evidence:** L0 | **Discovery ≠ Audit**

## Actual Architecture (from code)
- **Monolith:** `dashboard.py` (~156KB, 225 direct `@app` routes, 27 included routers)
- **Worker:** `microservices/worker_app.py` (4 routes)
- **Launcher:** `run_service.py` (web/aggregator/arbitrage/ingestion modes)
- **Top coupling:** `database` (327 imports), `bd_platform` (494), `cap646` (369)

## Reachability (§21)
| Classification | Count | Status |
|---|---|---|
| Entry points identified | 147 `__main__` + 2 FastAPI apps | DISCOVERED |
| Reachability proven | 0 | NOT VERIFIED |
| Dead/orphan modules | NOT VERIFIED | Wave 20 partial |

## Findings
- **WF-004** P2: Monolithic dashboard coupling
- **WF-005** P2: TODO/FIXME markers present

**Wave 2 CLOSED:** Architecture mapped; reachability NOT VERIFIED without runtime traces.
