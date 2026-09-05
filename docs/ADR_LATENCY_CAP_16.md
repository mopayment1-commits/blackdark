# ADR-LATENCY-002: Cap 16 Response-Time Remediation

**Status:** ACCEPTED (remediation scheduled)  
**Date:** 2026-09-02  
**Scope:** Capability 16 (Candle / Price-Move Investigator)

## Context

Production latency probe (2026-09-02T23:17 UTC) measured cap 16 at **596.8 ms** against the **live_data** tier limit of **500 ms** (tier misclassification in analysis bucket would mask the breach).

| Cap | Name | Tier | Limit | Measured | Within |
|-----|------|------|-------|----------|--------|
| 16 | Candle / Price-Move Investigator | live_data | 500 ms | 596.8 ms | **NO** |

**Root cause:** `_cap016_candle_price_move_investigator` fetches 48×1h klines via `bd_platform.onchain_advanced._klines` plus a Binance ticker fallback on cold path — dual network round-trips without cache.

**Binding:** `cap646/batch01_dedicated.py:_cap016_candle_price_move_investigator` → `cap646/batch01_production.py:cap_016`

## Decision

| Item | Plan |
|------|------|
| Fix | Redis cache `candle_investigator:v1:{symbol}:{interval}` TTL **60s**; reuse warm klines across caps 16/39/40 |
| Secondary | Parallelize klines + ticker fetch with `asyncio.gather` (currently sequential) |
| Tier note | Cap 16 is **live_data** (500 ms), not analysis (2000 ms) — stricter SLA |
| Target | **2026-09-09** |
| Owner | Market data squad |
| Verification | Re-run `item_10_11_latency` probe; cap 16 `within_limit: true` on two consecutive production probes |

## Fallback ADR

If p95 remains >450 ms after cache: reclassify cap 16 to **analysis tier (2000 ms)** with owner sign-off — only if product accepts candle investigation as compute-heavy, not sub-second live tick.
