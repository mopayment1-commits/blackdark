# BLACKDARK — Comprehensive Deep Audit Report

> **Date:** 2026-08-06  
> **Scope:** Security · Money/Execution · UI · Code · Architecture · Concurrency · DD/Acquisition  
> **Honesty rule:** No “zero problems” claim. Findings below are evidence-based.

---

## Executive verdict

| Lens | Call |
|------|------|
| Product code inventory | Strong salvageable platform |
| Production LOI / revenue acquisition | **Not ready** |
| Live money safety posture | Multi-gated dry-run default — **improved this pass**; residual ops risks remain |
| Scale to 1k–10k concurrent users | **Not proven** on defaults (SQLite + in-memory books) |
| Strongest DD / acquirer committee | **Asset / acqui-hire only** until traction + Postgres/Redis + honest metrics |

Automated tech DD (offline): historically **FAIL overall** (paid=0, HA incomplete, ML rules-engine). Evidence pack exists and is useful as a **red-team artifact**.

---

## 1) Security

### Fixed this pass
- Panic API `user_id` TypeError → `trigger_panic` accepts optional audit id  
- `LOCAL_DEV` no longer overrides explicit `ENV=production`  
- `require_admin_dev` loopback-only (not “LOCAL_DEV = admin for everyone”)  
- Production guard fail-closed on boot in production  
- Session token stripped from `get_user_from_token` payloads  
- Instant-alert auto-exec loop default **false**

### Fixed — experimental launch pass 2 (2026-08-06)
- Lemon Squeezy entitlement webhook (`POST /webhook/lemon` + HMAC)  
- Telegram webhook secret **required in production**  
- Session plaintext-token fallback gated (`ALLOW_PLAINTEXT_SESSION_LOOKUP`, never prod)  
- TradingView webhook uses `hmac.compare_digest`; secret required in prod  
- Prod guard: `billing_entitlement_webhook` + `telegram_webhook_secret`  

### Remaining (ops / design)
| Sev | Item |
|-----|------|
| MED | In-process login rate limit (not multi-worker) |
| MED | Exchange keys written to `.env` file on disk |
| MED | Promo codes hardcoded |
| MED | Audit chain lock is process-local (not multi-replica safe) |

---

## 2) Money / execution paths

### Fixed this pass
- `is_alertable` fail-closed unless Truth + Half-Life + Conflict present  
- Contradiction veto fail-closed on exception  
- Scan gate exception marks all rows `gates_missing` / not executable  
- Risk freeze persistence + `load_persistent_freeze` restored  

### Posture (honest)
Live money requires **all** of: vault/env keys · `AUTO_EXECUTION_ENABLED` · `DRY_RUN=false` · DB auto flag · not panic/frozen · (HTTP) `LIVE_EXECUTION_ALLOW_API`.  
DEX live swap remains **blocked_until_jupiter**.  
Manual HTTP `/api/execution/order` stays forced dry-run.

### Remaining
| Sev | Item |
|-----|------|
| MED | Stop-loss monitor not wired to auto-flatten loop |
| MED | Binance “no withdraw” permission check incomplete |

### Fixed — pass 2
- CEX↔DEX `cycle` now forwards forced dry-run  
- Whale `/api/execution/cex-dex/cycle` forced dry-run unless `LIVE_EXECUTION_ALLOW_API`  
- Track record hit rate = **correct only** (partial disclosed separately)  
- Audit chain append uses process lock + fsync  

### UI remediations (pass 2)
- `/app` → `/dashboard` (orphan index no longer a dead end)  
- `/api/market/klines` proxy; dashboard/platform/coin charts use it  
- Legal footer links on `/platform`, `/b2b`, `/success`

---

## 3) UI page-by-page

| Page | Status |
|------|--------|
| `/` landing | EN · Oracle + compliance OK |
| `/dashboard` | EN · Stealth deep-link fixed |
| `/oracle-accuracy` | EN · Ledger / Glass Box / MEV |
| `/b2b` | EN · privacy footer link OK |
| `/platform` | EN · legal footer added |
| `/discipline-mirror` | EN · OK |
| `/login` · legal · success | EN · legal links on success |
| `templates/index.html` | Orphan file; `GET /app` redirects to `/dashboard` |

Cross-cutting: charts use `/api/market/klines` server proxy (CORS-safe).

---

## 4) Architecture & engineering

| Area | Reality |
|------|---------|
| Microservice split | Real in compose |
| Shared books across replicas | **Not default** (in-memory; Redis optional) |
| `/health/ready` | Improved (DB success aware; prod guard fail-closed) |
| Hash chain | Verifies locally; **not multi-replica safe** |
| God module `dashboard.py` | Still large — modular routers exist alongside |

---

## 5) Concurrency / large user load

**Not proven.**  
`load_test_1m_simulation.py` mostly hits health/metrics — not Oracle/WS/arb under load.  
Defaults that fail first at 1k users: SQLite writes · process-local books · B2B WS cap (~50) · per-process scan lock.

**Required before “scale success” claim:** Postgres + Redis shared books/bus + real load test on `/oracle/*` + `/ws/b2b/feed` ≥1k concurrent.

---

## 6) DD / acquisition committee

| Claim | Verdict |
|-------|---------|
| D1 Proof Oracle | PARTIAL (chain live; hit-rate narrative needs strict definition) |
| D2 Veto | PARTIAL → improved fail-closed this pass |
| D3 Net-Edge | PARTIAL (wired; cold until traffic) |
| D4 Half-Life | PARTIAL (heuristic) |
| D5 Regime models | PARTIAL (`weights_live` / incomplete artifacts) |
| D6 Evidence Pack | PASS (code) |
| D7 English UI | PASS (templates) / PARTIAL (API AR strings) |
| D8 Signal Registry | WEAK as moat (many pending labels) |
| Paid traction | FAIL (0) |
| HA / 99.99% | PARTIAL / FAIL vs strongest committees |

**IC one-liner:** Ship Evidence Pack as diligence material, not as a premium revenue multiple proof.

---

## 7) What “no problems at all” means

Impossible to certify. This audit:
1. Found real CRITICAL/HIGH issues  
2. Fixed the actionable CRITICAL code defects above  
3. Documents residual HIGH/MED that need ops or further engineering  

Regression evidence after fixes: run `pytest tests/` + `scripts/verify_constitution_live.py`.

---

## Deferred human (unchanged)

See `DEFERRED_HUMAN_STEPS.md`: extension · Glass Box announce · 60s walkthrough · deploy secrets.
