# B9 Temporal Implementation Report

**Base SHA:** `aadf5da4` (B8 closed)  
**Status:** `PENDING_VERIFICATION`  
**Builder claim:** `PASS_ENGINEERING_NOT_CLAIMED`

## Quoted B9 scope (plan §4 + §10 + SPEC §18)

**§4 row:** `B9 | PLANNED_NOT_STARTED | §18 | 34, 35, 36, 51 | — | —`

**§10 detail:**
> ### B9 — Research / Explanation (`PLANNED_NOT_STARTED`)
> - **SPEC §:** 18
> - **Launch numbers:** 34, 35, 36, 51
> - **Status:** `PLANNED_NOT_STARTED`

**SPEC §18 rules (builder interpretation per fast-path command):** generation time, source snapshot time, validity window, stale/expiry threshold, no expired explanation presented as current, timezone display vs canonical instants.

## Entry gates — MET

| Gate | Status |
|------|--------|
| B8 `INDEPENDENT_VERDICT` = `PASS_ENGINEERING` | MET (`aadf5da4`) |
| B8 isolation leakage = 0 | MET |
| Scope = Launches #34, #35, #36, #51 only | MET |

## Implementation

| Module | Role |
|--------|------|
| `launch57/research_explanation_timing_common.py` | B9 canonical owner — explanation generation/validity timing |
| `launch57/b9_research_explanation_bridge.py` | B9 bridge — fail closed on expired explanations |
| `launch57/batch9_isolation.py` | Isolation envelope |
| `launch57/explanation_ai_common.py` | Auto-applies B9 for in-scope launch IDs |
| `launch57/explanation_ai_batch1.py` | Passes `params` into envelope for all #34–#36/#51 surfaces |

## Tests

```bash
python3 -m pytest tests/launch57/test_temporal_batch9.py tests/launch57/test_explanation_ai_batch1.py tests/launch57/test_temporal_batch8.py tests/launch57/test_temporal_batch4.py tests/launch57/test_temporal_batch5.py tests/launch57/test_temporal_batch6.py tests/launch57/test_temporal_batch7.py -q
```

61 passed, 0 failed.

## Residual risks (for IV)

- Explanations without explicit `source_age_ms` fall back to spine timestamp / `utc_now()` for generation time.
- Default validity window is 3600s; default stale threshold is 300s — overridable via payload/governed fields.
- `explanation_ai_batch1` still uses `cap646.evidence_class` compliance footer — pre-existing; B9 adds timing only.
- `#51` portal/reports surfaces may run without spine; timing uses generation-time fallback.
