# Retrospective 4-Way Reclassification — Batches 01–04 (400 capabilities)

**Audited at:** 2026-08-30T20:17:18.574901+00:00

## Cumulative (400 capabilities)

| Classification | Count | % |
|---|---:|---:|
| **VERIFIED-DEEP (native)** | **285** | 71.2% |
| **REUSED-LINK** | **51** | 12.8% |
| WRAPPER-ONLY-UNVERIFIED | 0 | 0.0% |
| DEFERRED/DELEGATED | 64 | 16.0% |

**Quad-passing total (native + reused):** 336

## Per batch

| Batch | Native | REUSED-LINK | Wrapper | Deferred |
|---|---:|---:|---:|---:|
| 01 (hero) | 43 | 44 | 0 | 13 |
| 02 (101–200) | 59 | 1 | 0 | 40 |
| 03 (201–300) | 87 | 2 | 0 | 11 |
| 04 (301–400) | 96 | 4 | 0 | 0 |

## Method

- Quad criteria unchanged (real code + independent test PASS + live OK + source traced).
- REUSED-LINK: quad pass + `merged_into` / `extends_ref` / `exact_fn_reuse` / heroes delegate.

Full JSON: `docs/RETROSPECTIVE_RECLASSIFICATION_BATCHES_01_04.json`
