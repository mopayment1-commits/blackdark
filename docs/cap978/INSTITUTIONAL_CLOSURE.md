# CAP978 — Institutional Closure Baseline

**Status:** INTERNAL CLOSURE COMPLETE (978 scope)  
**Source PDF:** `Project_978_Capabilities_Grouped_b618.pdf`  
**Catalog:** `CAP978_CATALOG.json` (646 base + 332 extension)

## Scope tiers (978 vs 826 vs 678)

| Tier | IDs | Count | Purpose |
|---|---:|---:|---|
| **Full catalog / `--full` gate** | 1–978 | 978 | Institutional closure baseline (PDF + frozen counts) |
| **Project delivery scope** | 1–826 | 826 | Agreed import/delivery (`646` base + extension `647–826`) |
| **CI sample / `sample=True`** | 1–646 + 647–678 | 678 | Fast structural gate (no live network) |

The **152 capabilities** with IDs **827–978** are real `extension_647_978` catalog rows (track T19). They are **outside the 826 delivery scope by design**, not a numbering gap or duplicate set. Full-mode gate (`--full`) scans all 978; routine CI uses the 678 sample.

Constants: `cap978/catalog.py` (`PROJECT_SCOPE_TOTAL`, `POST_PROJECT_EXTENSION_TOTAL`, `CI_SAMPLE_TOTAL`).

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
PYTHONPATH=/workspace python3 scripts/verify_institutional_closure.py --ci
PYTHONPATH=/workspace python3 scripts/verify_institutional_closure.py --full
curl /api/cap646/closure/978
curl /api/cap646/evidence-room
curl /api/cap646/institutional-gate
curl /api/cap646/commercial-launch
```

## Institutional gate

- Baseline tag: `cap978-closure-v1`
- Gate module: `cap978/institutional_gate.py`
- CI sample gate: `scripts/verify_institutional_closure.py --ci`
- Full baseline lock: `scripts/verify_institutional_closure.py --full`
- Commercial checklist: `docs/cap978/COMMERCIAL_LAUNCH_CHECKLIST.json`
- Soft launch closure: `docs/cap978/SOFT_LAUNCH_CLOSURE.md` + `scripts/run_soft_launch_closure.py`

## EXTERNAL only (human/vendor — not internal code closure)

See `EXTERNAL_REGISTRY.json` — 31 capability slots + 4 governing controls requiring external contract, IdP, or attestation (35 registry rows total).

## Platform integration

Raw → Derived → Entity/Event → Feature → Signal → Prediction/Decision → Confidence → User Exposure → Outcome → Evidence/Error → Learning → Model Version

Verified via `platform_chain_e2e.py` and `/api/cap646/platform-chain/e2e`.
