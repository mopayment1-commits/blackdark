# ADR-004: Institutional Flows Dual Insert API (Justified-Retain)

## Status
Accepted — CLOSURE-MANDATE-VERIFY database dedup closure

## Context
`database.py` exposed two insert paths for `institutional_flows`:
- `insert_institutional_flow(...)` — single-row `execute`, returns `lastrowid`
- `insert_institutional_flows(rows)` — bulk `executemany`, no per-row IDs

jscpd flagged duplicated INSERT SQL (case 14). SQL text is now SSOT via
`_INSTITUTIONAL_FLOWS_INSERT_SQL`. The dual **API** remains because write
patterns and caller contracts differ materially.

## Measured evidence (SQLite, local bench 2026-09-02)

| Batch size | Loop `execute` (ms) | `executemany` (ms) | Speedup |
|-----------:|--------------------:|-------------------:|--------:|
| 1 | 0.066 | 0.032 | 2.1× |
| 10 | 0.307 | 0.043 | 7.2× |
| 50 | 1.461 | 0.117 | 12.5× |
| 200 | 5.796 | 0.391 | 14.8× |

**Typical production batch:** `whale_tracker.persist_manipulation_alerts` /
`persist_sector_inflow_index` insert **N alerts per detection cycle** (often
10–200 rows). Single-row path serves API/tests requiring `lastrowid`.

Unifying both into loop-`execute` would regress bulk ingest by **7–15×** at
observed batch sizes. Unifying into `executemany` only would break callers
needing `lastrowid` from `insert_institutional_flow`.

## Decision
1. **Eliminate** SQL duplication — `_INSTITUTIONAL_FLOWS_INSERT_SQL` constant.
2. **Justified-Retain** dual public APIs — not Tolerate, not generic Invest:
   - Single path: latency + `lastrowid` contract
   - Batch path: `executemany` throughput for whale/sector ingest

## Alternatives rejected
| Alternative | Why rejected |
|-------------|--------------|
| Single function, always loop `execute` | 7–15× slower on whale_tracker batches |
| Single function, always `executemany` | Cannot return `lastrowid` for single-row API |
| Tolerate duplicate SQL | Violates CLOSURE-MANDATE; no sunset |

## Consequences
- jscpd case 14 SQL clone: **0** (Eliminate)
- Public API surface unchanged (backward compatible)
- Lock table row: **Justified-Retain** with this ADR as evidence
