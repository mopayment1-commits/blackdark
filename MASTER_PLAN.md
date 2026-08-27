# BLACKDARK — Master Execution Plan

**Governing principle:** DON'T DELETE KNOWLEDGE — COMPOUND IT  
**Rule:** Execute **one wave at a time**. Do not start Wave N+1 until Wave N is implemented, tested, runtime-verified, and explicitly confirmed.

---

## Wave 0 — Security & Performance Hardening

**Goal:** Harden the institutional compounding surface (Phases 1–8) against abuse, timing leaks, and performance regression before scaling traffic.

### Security deliverables

| # | Item | Acceptance |
|---|------|------------|
| S1 | Request body size cap on institutional write APIs (64KB default) | POST >64KB → HTTP 413 |
| S2 | Stricter rate limits on audit export + institutional writes | `/api/audit/export` 20/min; writes 40/min |
| S3 | `X-Response-Time` + slow-request metrics (≥500ms warn, ≥2000ms alert) | Header present; `slow_requests_total` increments |
| S4 | Cache-Control on public verify/read endpoints (30s) | `/api/compounding/_verify` returns max-age=30 |
| S5 | `GET /api/security/wave-00` status endpoint | Returns checks + version |
| S6 | Cross-Origin-Resource-Policy: same-site header | Present on all responses |
| S7 | ZAP baseline re-scan (production URL) | No new HIGH/CRITICAL vs baseline |

### Performance deliverables

| # | Item | Acceptance |
|---|------|------------|
| P1 | k6 Wave 0 script (`scripts/k6_wave_00_hardening.js`) | fast paths p(95)<200ms after warmup |
| P2 | Warm-up pass excludes cold-start from scoring | setup() preloads paths |
| P3 | Institutional verify path in k6 suite | `/api/compounding/_verify` included |
| P4 | Document results in `WAVE_00_HARDENING.md` | k6 + ZAP + curl pasted |

### Out of scope (Wave 0)

- Human pentest execution
- CDN/WAF activation (operator)
- Wave 1+ features

---

## Wave 1 — Data Engine Sprint 1 (IMPLEMENTED — pending production proofs)

> **Status:** Code merged (PR #92); bootstrap ingest + curl/k6 proofs in progress.  
> **Governing baseline:** [`BLACKDARK_CONTEXT.md`](BLACKDARK_CONTEXT.md) — institutional verdict remains **NOT READY**.

**Goal:** Foundational data collection and provenance layer (OHLCV, funding, open interest, events).

| Deliverable | Path |
|-------------|------|
| 10 SQL migrations | `blackdark/data/migrations/001-010_*.sql` |
| 7 API endpoints | `/api/v1/data/*` |
| APScheduler jobs | Binance OHLCV 1m/1h, funding, CoinGecko |
| Backfill CLI | `python -m blackdark.data backfill` |
| Evidence doc | `WAVE_01_DATA_ENGINE.md` |

### Out of scope (Wave 1)

- Distribution & growth instrumentation (deferred)
- Multi-region HA (Wave 3)

---

## Wave 2 — Corporate Due-Diligence Automation (PENDING)

> **Status:** NOT STARTED.

- Scheduled DATA_ROOM snapshot refresh
- Revenue quality live PSP integration (EXTERNAL_DEPENDENCY)

---

## Wave 3 — Multi-Region HA Proof (PENDING)

> **Status:** NOT STARTED.

- Signed load-test row in `LOAD_TEST_RUN_LOG.md`
- Postgres+Redis multi-worker staging proof

---

## Verification commands (Wave 0)

```bash
pytest tests/test_wave_00_hardening.py -v
k6 run -e MODE=fast -e BASE=https://blackdark-production.up.railway.app scripts/k6_wave_00_hardening.js
RUN_ZAP=1 TARGET_URL=https://blackdark-production.up.railway.app bash scripts/run_wave_00_zap.sh
curl -sS "$BASE/api/security/wave-00" | jq .
```

---

*Update this file only when a wave is completed and the next wave is explicitly approved.*
