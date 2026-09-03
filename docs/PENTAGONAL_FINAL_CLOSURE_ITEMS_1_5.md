# Pentagonal Final Closure — Items 1–5 (Direct Evidence)

**Generated:** 2026-09-02T23:16 UTC  
**Branch:** `cursor/pentagonal-hero-binding-e85e`  
**Production:** https://blackdark-production.up.railway.app

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

Over-limit caps (latest probe): **2, 3** (analysis tier), **16** (live_data tier). Cap **54** within limit but borderline.

| Cap | ADR | Fix | Target |
|-----|-----|-----|--------|
| 2, 3 | `docs/ADR_LATENCY_CAPS_2_3_54.md` | Redis wallet profiler cache | 2026-09-09 |
| 16 | `docs/ADR_LATENCY_CAP_16.md` | Redis candle cache + parallel fetch | 2026-09-09 |
| 54 | `docs/ADR_LATENCY_CAPS_2_3_54.md` | Warm global_liquidity cache | 2026-09-16 |

---

## Cap #56 — Authoritative Binding

**Bound to Single-Sentence Oracle: YES. Bound to Arbitrage Scanner: NO.**

Wrong source corrected: `PENTAGONAL_TEMPLATE_1_100.json` row #56 had `e2e_test: verify_official_batch02_production.py` — corrected to `batch01`. See `docs/CAP_56_HERO_BINDING_CORRECTION.md`.

---

## Arbitrage Scanner — Truth Path Fix

Root cause of 100% `missing_net_profit`: Oracle directional paths polluted cumulative `/api/oracle/net-edge-truth` stats — **not** missing net_profit in arb scan rows.

Fix: `GET /api/arbitrage/scanner/status` (current scan summary). Arb rows include `net_profit_usdt`; reject reasons are economics gates (e.g. `missing_withdrawal_fee`, `residual_edge_below_threshold`).

---

## B2B Feed Empty State

`record_count: 0` is **normal** when no manipulation/SII rows exceed thresholds. `empty_state` block added to feed payload (Whale analogy documented).

---

## Test Count

| Commit | Count | Added |
|--------|-------|-------|
| `b012e3b` | 21 | PSI/lookahead/LOO closure tests + `test_local_hero_endpoints` |
| `f6346f2` | 22 | `test_supplemental_closure_report` (intentional) |
| current | 25 | `test_cap56_oracle_binding_only`, `test_directional_oracle_does_not_pollute_truth_stats`, `test_b2b_feed_empty_state_block` |


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
