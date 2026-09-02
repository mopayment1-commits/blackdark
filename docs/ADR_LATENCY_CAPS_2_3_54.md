# ADR-LATENCY-001: Caps 2, 3, 54 Response-Time Remediation

**Status:** ACCEPTED (remediation scheduled)  
**Date:** 2026-09-02  
**Scope:** Capabilities 2 (Wallet Profiler), 3 (Wallet Profiler for Token), 54 (Global Liquidity Intelligence)

## Context

Production latency probe (2026-09-02T23:01 UTC) measured 100 capabilities against Nielsen-adapted tiers:

| Cap | Name | Tier | Limit | Measured | Within |
|-----|------|------|-------|----------|--------|
| 2 | Wallet Profiler | analysis | 2000 ms | 2142 ms | **NO** |
| 3 | Wallet Profiler for Token | analysis | 2000 ms | 2336 ms | **NO** |
| 54 | Global Liquidity Intelligence | analysis | 2000 ms | 1634 ms | YES (borderline 82%) |

Caps 2 and 3 exceed the analysis tier on cold-cache first request. Cap 54 is within limit but near ceiling; prior probe runs showed occasional >2000 ms under cold DeFiLlama aggregation.

## Decision

### Cap 2 — Wallet Profiler

| Item | Plan |
|------|------|
| Root cause | Multi-hop wallet graph aggregation without warm Redis cache |
| Fix | Add `wallet_profiler:v1:{address}` Redis TTL 120s; pre-warm top-50 whale addresses on deploy |
| Target | **2026-09-09** |
| Owner | Platform data engineering |

### Cap 3 — Wallet Profiler for Token

| Item | Plan |
|------|------|
| Root cause | Token-scoped holder graph + PnL rollup on cold path |
| Fix | Shared cache layer with cap 2 + token-scoped key `wallet_token_profiler:v1:{token}:{address}` TTL 90s |
| Target | **2026-09-09** |
| Owner | Platform data engineering |

### Cap 54 — Global Liquidity Intelligence

| Item | Plan |
|------|------|
| Root cause | DeFiLlama + cross-chain TVL aggregation on cold cache |
| Fix | Warm `global_liquidity:v1` cache TTL 300s at startup; lazy refresh background task |
| Fallback ADR | If p95 remains >1800 ms after cache: accept permanent **analysis-tier exception** at 2500 ms with owner sign-off (documented in ACCEPTED_RISK_REGISTRY) |
| Target | **2026-09-16** (cache); ADR exception review **2026-09-23** if needed |
| Owner | Macro intelligence squad |

## Verification

Re-run `scripts/generate_supplemental_closure_report.py` → `item_10_11_latency` after each fix. Gate: all three caps `within_limit: true` on two consecutive production probes.
