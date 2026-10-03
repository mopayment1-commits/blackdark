# Batch01 Institutional Closure — IDs 1–25

**Date:** 2026-09-11  
**Standard:** `BLACKDARK_Institutional_Capability_Standard_2026_v6` §2.1  
**Scope:** Official batch01 only (25 capabilities). **Does not claim 826/826 completion.**

## Verdict

| Metric | Value |
|--------|-------|
| PASS_INSTITUTIONAL (strict) | **25 / 25** |
| Deep semantic tests | **75 / 75** passed |
| Committee-ready batch01 | **Yes** (engineering scope) |
| PASS_LIVE | **Excluded** (no live deploy) |

## Methodology (not shallow execute-only)

Each capability 1–25 must pass:

1. Dedicated handler in `cap646/batch01_dedicated.py` (no `invoke_substantive` generator)
2. Production spine `cap646.batch01_production` with `binding_source=explicit_option_a`
3. Goal-specific domain payload keys (see `cap646/batch01_closure_spec.py`)
4. All 13 v6 gates via `cap646/batch_institutional_closure.verify_batch01_institutional`
5. Deep tests in `tests/cap646/test_batch01_institutional_deep.py`

## Evidence artifacts

| Artifact | Purpose |
|----------|---------|
| `docs/BATCH01_INSTITUTIONAL_CLOSURE_1_25.json` | RTM + per-gate evidence |
| `tests/cap646/test_batch01_institutional_deep.py` | Semantic regression (G03/G11/G13) |
| `tests/cap646/test_batch01_from_scratch.py` | From-scratch + v6 true gates |

## Verify

```bash
python3 scripts/batch01_institutional_closure.py
python3 -m pytest tests/cap646/test_batch01_institutional_deep.py -q
python3 -m pytest tests/cap646/test_batch01_from_scratch.py -q
```

## Next

Batch02 (IDs 26–50) — same strict process before any aggregate 826 claim.
