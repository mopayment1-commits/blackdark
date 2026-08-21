# CAP978 — Institutional Closure Baseline

**Status:** INTERNAL CLOSURE COMPLETE (978 scope)  
**Source PDF:** `Project_978_Capabilities_Grouped_b618.pdf`  
**Catalog:** `CAP978_CATALOG.json` (646 base + 332 extension)

## Verdict

| Classification | Count |
|---|---:|
| VERIFIED_COMPLETE | 910 |
| CANONICALLY_COVERED | 37 |
| EXTERNAL_BLOCKED | 29 |
| EXTERNAL_EVIDENCE_REQUIRED | 2 |
| **Internal incomplete** | **0** |

## Reproducible evidence

```bash
PYTHONPATH=/workspace pytest tests/cap646/ -q
PYTHONPATH=/workspace python3 scripts/run_institutional_evidence_room.py
curl /api/cap646/closure/978
curl /api/cap646/evidence-room
```

## EXTERNAL only (human/vendor — not internal code closure)

See `EXTERNAL_REGISTRY.json` — 31 capability slots + 4 governing controls requiring external contract, IdP, or attestation (35 registry rows total).

## Platform integration

Raw → Derived → Entity/Event → Feature → Signal → Prediction/Decision → Confidence → User Exposure → Outcome → Evidence/Error → Learning → Model Version

Verified via `platform_chain_e2e.py` and `/api/cap646/platform-chain/e2e`.
