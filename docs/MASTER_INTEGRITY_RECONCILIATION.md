# Master integrity reconciliation (576 unique IDs)

**Generated:** 2026-08-31T09:50:55.620676+00:00

> Of 576 re-audited unique capabilities, 4 (0.69%) are PRODUCTION-ALIGNED with fully matching production path.

## Master reconciliation table

| Classification | Count |
|----------------|------:|
| `PRODUCTION-ALIGNED` | 4 |
| `SPLIT-BRAIN-UNVERIFIED` | 202 |
| `DEFERRED/TEMPLATE-STUB` | 307 |
| `DEFERRED-EARLY-BATCH` | 57 |
| `EXTENSION-PENDING-CAP646` | 6 |
| **TOTAL** | **576** |

**Automated verification:** `all_checks_passed=True`

## DEFERRED-EARLY-BATCH (57) — primary batch partition

| Primary batch | Count |
|---------------|------:|
| `batch01` | 6 |
| `batch02` | 40 |
| `batch03` | 11 |

11+40+11=62 counts IDs in every evidence file they appear in. Five IDs are duplicated across files (b01∩b02: 126,164,183; b01∩b03: 224,245). 62-5=57 global unique.

## pytest

`2189 passed, 2 skipped, 4 deselected, 9739 warnings in 168.96s (0:02:48)`
