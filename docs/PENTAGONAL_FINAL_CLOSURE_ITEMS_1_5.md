# Pentagonal Final Closure — Items 1–5 (Direct Evidence)

**Generated:** 2026-09-02T23:16 UTC  
**Branch:** `cursor/pentagonal-hero-binding-e85e`  
**Production:** https://blackdark-web-production.up.railway.app

---

## Item 5 — PSI Threshold Confirmation (Final Report)

| Metric | Value |
|--------|-------|
| Feature | `onchain_netflow` |
| Corrected PSI | **0.9104** |
| Default threshold | 0.25 → **EXCEEDED** (3.64×) |
| Custom threshold | 0.75 → **EXCEEDED** (1.21×) |
| Classification | `monitor_elevated` |
| `custom_threshold_closure_status` | **NOT_CLOSED** |
| `predict_direction` frozen | **false** |

**Explicit statement:** `monitor_elevated` is **not** full institutional closure. PSI 0.9104 remains above the custom 0.75 threshold. Scheduled review: 2026-09-09 and 2026-09-16. Escalation if PSI > 1.0.

ADR: `docs/ADR_PSI_ONCHAIN_NETFLOW_MONITOR_ELEVATED.md`

---

## Item 1 — Latency Remediation ADR

Over-limit caps (latest probe 2026-09-02T23:15 UTC): **2, 3** (analysis tier). Cap **54** within limit (1606 ms) but borderline — preventive cache plan scheduled.

ADR: `docs/ADR_LATENCY_CAPS_2_3_54.md`

| Cap | Fix | Target |
|-----|-----|--------|
| 2 | Redis `wallet_profiler:v1` TTL 120s + pre-warm | 2026-09-09 |
| 3 | Token-scoped cache TTL 90s | 2026-09-09 |
| 54 | Warm `global_liquidity:v1` TTL 300s | 2026-09-16 |

Note: Cap 16 (live_data, 596 ms > 500 ms) also over limit — outside original 2/3/54 scope.

---

## Item 3 — Cap #69 Dual-Path (NOT GET Bypass)

| Event | Commit | UTC |
|-------|--------|-----|
| Dual-path introduced | `9746f81` | 2026-09-01T08:27:21Z |
| Facade fix (SSOT) | `b6d11a9` | 2026-09-01T23:05:44Z |
| Exposure window | ~14h 38m | |

**Paths during window:**
- A: `execute_capability(69)` → `batch02 cap_069`
- B: `handle_onchain_capability(69)` → `build_cross_domain_decision_payload`

**Heroes affected:** Oracle + Arbitrage Scanner (cap 69 binding). Other four heroes unaffected.

**Post-fix:** `onchain.py:52-55` delegates to `batch02_execute(69)`. Test: `tests/cap646/test_cap69_dual_path.py`.

GET entitlement bypass (PR #358) is a **separate** issue — see `docs/GET_ENTITLEMENT_PRODUCTION_CLOSURE.json`.

---

## Items 1, 2, 4 — Full Tables

Full 100-row latency table, 81-link hero map, and 6 hero live response bodies are embedded in `docs/SUPPLEMENTAL_CLOSURE_REPORT_1_18.json`:

- `item_10_11_latency.rows` (100 rows)
- `item_12_hero_map_final.heroes` (81 links)
- `item_15_live_heroes_full` (6 full bodies)
