# Batches 01–02 — current classification distribution

**Generated:** 2026-08-31T09:28:17.838007+00:00

## Historical vs current

- **97 VERIFIED-DEEP** = pre-reclassification unique count (methodology difference; see note in JSON).
- **200 audit rows** = `RETROSPECTIVE_DEEP_AUDIT_BATCHES_01_02.json` (109 batch-01 + 91 batch-02-only).

## Current distribution (200 audit rows)

| Classification | Count |
|----------------|------:|
| `DEFERRED-EARLY-BATCH` | 51 |
| `EXTENSION-PENDING-CAP646` | 6 |
| `SPLIT-BRAIN-UNVERIFIED` | 143 |

## DEFERRED-EARLY-BATCH vs SPLIT-BRAIN B/C/D

DEFERRED-EARLY-BATCH (57 unique across ALL batches 01-06; was 58 before #725 moved to EXTENSION-PENDING-CAP646) is NOT the same as SPLIT-BRAIN B/C/D (58). Zero ID overlap. Prior label DEFERRED/DELEGATED was misleading when described as 'from batches 01-02 only' — actual split: b01=11, b02-range=40, b03=11 unique (evidence files).

**By evidence file (unique IDs):**

- batch-01 file: `{'SPLIT-BRAIN-UNVERIFIED': 83, 'DEFERRED-EARLY-BATCH': 11, 'EXTENSION-PENDING-CAP646': 6}`
- batch-02 file (101–200): `{'SPLIT-BRAIN-UNVERIFIED': 60, 'DEFERRED-EARLY-BATCH': 40}`

