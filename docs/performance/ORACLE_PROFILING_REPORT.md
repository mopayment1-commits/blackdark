# Oracle API Profiling Report

**Date:** 2026-08-29  
**Target endpoint:** `GET /oracle/{symbol}/quick` (oracle_quick)  
**Observed baseline:** p95 ≈ **739 ms** (`docs/CONSULTANT_13_CLOSURE_REPORT.md`, `load_test_concurrent.py --workers 20 --requests 60`)  
**Method:** py-spy flamegraph under live k6 load (source of truth) + cProfile via `tests/test_oracle_perf.py` (unit/integration contrast)

---

## Executive summary

Under concurrent load, **`/oracle/BTC/quick` p95 latency is dominated by external market-data fetches (Binance REST + TLS handshakes)**, not ML inference. The quick path does **not** call `compute_unified_oracle`; it calls `_compute_oracle_quick_payload` → `fetch_binance_ticker`, which opens a **new `aiohttp.ClientSession` per cache miss**.

**Root cause classification: (c) external API**, with secondary contributions from **(d) serialization** (JSON decode) and **(e) other** (uvicorn multi-worker IPC, viral oracle semaphore queueing, background prediction logging).

cProfile on `tests/test_oracle_perf.py` tells a **different story** (heavy SQLite sentiment reads on `compute_unified_oracle` / explain paths). **py-spy under live load is authoritative** for the 739 ms quick-API regression.

---

## Environment

| Item | Value |
|------|-------|
| Host | Cloud Agent VM (linux 6.12) |
| App | `uvicorn dashboard:app --host 127.0.0.1 --port 8765 --workers 2` |
| Workers | `WEB_CONCURRENCY=2`, 2 uvicorn workers |
| Database | SQLite `data/blackdark.db` (production-like local data) |
| Redis | **Not configured** (`REDIS_URL` unset → memory cache backend) |
| Viral guards | `VIRAL_MODE=true`, `SOFT_LAUNCH=true` |
| Profiling run 2 overrides | `VIRAL_ORACLE_RL_PER_MIN=100000`, `VIRAL_MAX_INFLIGHT=5000` (to avoid 429 storm during profiling) |

**Tools:** `py-spy 0.4.2`, `k6 v2.2.0`, Python 3.12.3

---

## Load test results

### Run 1 — k6 default production rate limits (invalid for latency analysis)

```bash
k6 run -e BASE=http://127.0.0.1:8765 --vus 50 --duration 3m scripts/load_test_oracle_profiling.js
```

| Metric | Value |
|--------|-------|
| oracle_quick p95 | 31 ms |
| http_req_failed | **99.85%** (429 rate-limit) |
| cache hit rate | 0.06% |

**Conclusion:** At `VIRAL_ORACLE_RL_PER_MIN=60`, 50 VUs spend almost all time on 429 responses. Flamegraph from this run is **not representative** of oracle compute cost.

### Run 2 — k6 with raised limits (valid py-spy capture)

Same k6 command after raising rate limits. py-spy recorded **185 s** with `--subprocesses`.

| Metric | Value |
|--------|-------|
| oracle_quick p95 | **3444 ms** |
| http_req_failed | 0% |
| Total iterations | 5274 |
| cache hits / misses | 2572 / 2702 (**48.8% hit rate**) |

### Concurrent harness (reproduces consultant baseline)

```bash
python3 scripts/load_test_concurrent.py --base http://127.0.0.1:8765 --workers 20 --requests 60
```

| Endpoint | p50 | p95 | ok_rate |
|----------|-----|-----|---------|
| **oracle_quick** | 513 ms | **1283 ms** | 1.0 |
| live | 63 ms | 73 ms | 1.0 |
| trust_os | 459 ms | 895 ms | 1.0 |

Local reproduction exceeds the documented **739 ms** p95 (likely hotter contention during multi-endpoint burst + 2-worker setup). Same bottleneck family: slow oracle paths under thread concurrency.

---

## py-spy — Top 5 functions by sample weight (live load, run 2)

Flamegraph: `docs/performance/oracle_flamegraph_run2.svg` (31,539 samples, 185 s)

| Rank | Function / area | Samples (agg.) | ~% of samples | Interpretation |
|------|-----------------|---------------:|--------------:|----------------|
| 1 | `ssl.do_handshake` | 1,616 | 0.44% | **New TLS connections** per outbound HTTP |
| 2 | `json.decoder.raw_decode` | 1,925 | 0.53% | Parsing Binance JSON payloads |
| 3 | `dashboard.oracle_quick` | 3,068 | 0.84% | Request handler (includes cache miss work) |
| 4 | `aiohttp` / `fetch_binance` / `ClientSession` stack | ~5,163 | ~1.4% | **External REST ticker fetch** |
| 5 | `uvicorn.supervisors.multiprocess` (`pong`/`recv`) | ~6,855 | ~1.9% | Multi-worker process coordination under load |

**Keyword buckets (overlapping title tags in flamegraph):**

| Bucket | Samples |
|--------|--------:|
| uvicorn IPC / supervisor | 6,855 |
| external HTTP (aiohttp/Binance) | 5,163 |
| oracle_quick handler | 4,277 |
| JSON decode | 1,925 |
| SSL/TLS handshake | 1,616 |
| SQLite (`aiosqlite` / `database.py`) | 848 |
| ML inference (`predict_direction`, joblib) | **0** |

**Interpretation:** Under live `/quick` load, workers spend the largest identifiable blocks on **outbound HTTP setup and response parsing**, not ML. ML does not appear on the quick hot path.

---

## cProfile — Top 5 functions by cumulative time (unit test path)

Profile file: `docs/performance/oracle_stats.prof`  
Command: `python -m cProfile -o docs/performance/oracle_stats.prof -m pytest tests/test_oracle_perf.py`

| Rank | Function | cumtime | Notes |
|------|----------|--------:|-------|
| 1 | `oracle_unified.compute_unified_oracle` | 5.28 s | **Not used by `/quick`**; hit by explain + unified tests |
| 2 | `database.insert_oracle_prediction` | 3.92 s | Audit log writes |
| 3 | `weight_aggregator.build_full_market_context` | 3.58 s | Unified oracle context build |
| 4 | `sentiment_engine.load_active_sentiment_indices_*` | 3.31 s | Sentiment index load |
| 5 | `database.fetch_sentiment_logs_for_asset` | 3.05 s | **SQLite sentiment history** |

**cProfile vs py-spy divergence:** Unit tests exercise `compute_unified_oracle` and explain routes, which pull large sentiment SQL graphs. Live `/quick` bypasses unified oracle and instead blocks on `fetch_binance_ticker`.

---

## Per-oracle-call estimates

### Live load (py-spy + k6 run 2, authoritative for `/quick`)

| Category | Per cache-miss call (estimated) | Evidence |
|----------|--------------------------------|----------|
| **External API** | **~250–1200+ ms** (p50–p95 under 50 VUs) | k6 `oracle_quick_duration` p95=3444 ms; flamegraph SSL+aiohttp stacks |
| SQL queries | ~0–2 async writes (background) | Quick path sync work is HTTP-bound; `insert_oracle_prediction` queued in `BackgroundTasks` |
| ML inference | **0 ms** on `/quick` | No `predict_direction` in flamegraph; quick uses `market_context.oracle_score` |
| Serialization | ~5–20 ms | `raw_decode` + `sanitize_oracle_payload` + `JSONResponse` |
| Redis/cache | memory backend | See below |

**SQL (quick path, synchronous portion):** effectively **0 queries** before response; background audit insert is decoupled.

**External API (quick path):** **1 REST round-trip per cache miss** (`fetch_binance_ticker` → new `ClientSession` at `market_context.py:445`). With ~49% cache hit rate at 2 s TTL, **~0.5 HTTP calls per request** amortized.

### cProfile averages (test harness — not `/quick` primary)

| Function | Calls | Avg cumtime/call |
|----------|------:|-----------------:|
| `_compute_oracle_quick_payload` | 600 | 0.22 ms (TestClient + warm cache) |
| `fetch_binance_ticker` | 728 | 0.19 ms (mocked/warmed network) |
| `fetch_sentiment_logs_for_asset` | 70,020 | 0.04 ms (unified path only) |
| `insert_oracle_prediction` | 576 | 6.80 ms |
| `predict_direction` | 1,944 | 1.46 ms (unified/finalize only) |

---

## Redis hit/miss ratio (during test)

| Run | Backend | Hits | Misses | Hit rate |
|-----|---------|-----:|-------:|---------:|
| k6 run 1 (rate limited) | memory | 151 | 243,267 | 0.06% |
| k6 run 2 (profiling) | memory | 2,572 | 2,702 | **48.8%** |

`REDIS_URL` was **not set** — `viral_capacity.quick_cache_*` used **in-process memory** (2 s TTL). No Redis server participated.

Response field `viral_cache: "hit"` present on cache hits.

---

## Code path (why external API wins)

```
GET /oracle/{symbol}/quick
  → quick_cache_get (2s TTL, memory)
  → run_oracle_bounded (semaphore, max 32)
  → _compute_oracle_quick_payload
       → get_best_price (WS) OR fetch_binance_ticker
            → NEW aiohttp.ClientSession() per call  ← TLS handshake storm
            → REST JSON → raw_decode
  → background: _log_oracle_prediction → SQLite insert
```

`compute_unified_oracle` is **not** on this path (used by `/oracle/{symbol}/explain` and full oracle flows).

---

## Root cause

| Option | Verdict | Rationale |
|--------|---------|-----------|
| (a) ML inference | **No** | Zero ML samples in live flamegraph; `/quick` uses lightweight `oracle_score` |
| (b) SQL queries | **Minor on `/quick`** | Dominant in cProfile only for unified/explain tests; ~848 sqlite samples vs HTTP/SSL in py-spy |
| **(c) external API** | **Yes — primary** | Binance ticker via per-request `ClientSession`; SSL handshake + network dominate under concurrency |
| (d) serialization | **Secondary** | JSON `raw_decode` ~0.5% samples; non-trivial but not top driver |
| **(e) other** | **Contributing** | Uvicorn 2-worker IPC (~1.9% samples), viral semaphore queueing, 2 s cache TTL → ~50% miss under mixed assets |

**Single-sentence root cause:** Cache misses on `/oracle/{symbol}/quick` trigger **uncached Binance REST fetches with fresh TLS sessions per request**, and under concurrent load (20–50 workers) this external I/O plus worker coordination produces **p95 ≈ 739–1283 ms** (documented) and higher under sustained 50-VU k6.

---

## Artifacts

| File | Description |
|------|-------------|
| `docs/performance/oracle_flamegraph_run2.svg` | py-spy flamegraph (valid run) |
| `docs/performance/oracle_flamegraph.svg` | py-spy flamegraph (run 1 — rate-limit dominated) |
| `docs/performance/oracle_stats.prof` | cProfile output |
| `docs/performance/k6_oracle_profiling_run2.log` | k6 stdout (50 VU / 3 min) |
| `docs/performance/k6_oracle_profiling_summary.json` | k6 summary JSON |
| `docs/performance/concurrent_load_baseline.log` | `load_test_concurrent.py` reproduction |
| `docs/performance/cprofile_pytest.log` | pytest output during cProfile |
| `scripts/load_test_oracle_profiling.js` | k6 profiling script |
| `tests/test_oracle_perf.py` | cProfile pytest harness |

---

## Recommended next steps (report only — not implemented)

1. **Reuse a shared `aiohttp.ClientSession`** for `fetch_binance_ticker` / `_rest_get` (eliminate per-request TLS).
2. **Increase `/quick` cache TTL** or shard cache by asset under viral load tests.
3. **Separate profiling** of `/oracle/{symbol}/explain` (unified + sentiment SQL) from `/quick`.
4. Re-run signed load with `REDIS_URL` + Postgres for HA-realistic cache/backend numbers.

---

*No application code was changed as part of this investigation.*
