# Feature #001 / #002 — G3 Reliability Soak Test Report

**Status:** ⏳ **IN PROGRESS** (soak running — do not stop)  
**Prerequisite:** G2 ✅ PASS (`g2_run_20260730_155520.json`)

> **Feature #1 and #2 remain NOT COMPLETE** until G3 + all Quality Gates (G1–G9) pass.

---

## Assessment Framework

### 1. Environment Baseline
Captured at soak start → `HOURLY_OPERATION_REPORTS/baseline_<run_id>.json`

- Platform / Python / CPU / memory
- Env vars (WS, Redis, venues, symbol limit)
- Exchange venue policy

### 2. Performance Trend (Hour 1 → 6 → 12 → 18 → 24)
- Memory growth %
- Latency drift % (p95)
- Queue HWM growth %
- Tick processing degradation %
- WS instability trend

### 3. Reliability Trend
- Stream connected ratio
- Failover activations per hour
- Instability events (reconnects + frozen)

### 4. Data Integrity Trend
| Metric | Source |
|--------|--------|
| Missing ticks % | gap_alerts / ticks processed |
| Duplicate ticks % | duplicates_prevented / ticks |
| Out-of-order ticks % | sequence_violations / ticks |
| Rejected ticks % | sanitize rejects / ticks |
| Stale data % | stale_quotes / symbol_count |
| Exchange divergence % | BTC mid spread across venues (bps) |

### 5. Recovery Trend
| Metric | Source |
|--------|--------|
| Disconnect count | total_reconnects + stale_reconnects Δ |
| Avg reconnect time | ws_stream_resilience backoff samples |
| Max reconnect time | ws_stream_resilience max delay |
| Failed reconnect attempts | disconnected streams at snapshot |
| Data recovery completeness % | recovery_actions / gap_alerts |

---

## Hourly Reports

`HOURLY_OPERATION_REPORTS/hourly_<run_id>_hXX.json`

Milestone trend updates: Hours **1, 6, 12, 18, 24**

---

## After 24 Hours — Final Report

```bash
python scripts/g3_reliability_soak_test.py --finalize
```

Issues:
- Performance trend
- Reliability trend
- Data integrity trend
- Recovery trend
- **Final G3 PASS/FAIL decision**

Also available during soak (partial):
```bash
python scripts/g3_reliability_soak_test.py --analyze-trend
```

---

## G3 Verdict

## ⏳ G3: IN PROGRESS

Awaiting 24/24 hourly snapshots + final `--finalize`.
