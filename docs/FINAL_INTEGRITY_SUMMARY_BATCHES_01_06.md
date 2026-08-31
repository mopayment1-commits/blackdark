# Final integrity summary — hero batches 01–06

**Generated:** 2026-08-31T09:01:43.778741+00:00

## Classification counts (unique IDs)

| Classification | Count |
|----------------|------:|
| `DEFERRED/DELEGATED` | 58 |
| `DEFERRED/TEMPLATE-STUB` | 307 |
| `EXTENSION-PENDING-CAP646` | 5 |
| `PRODUCTION-ALIGNED` | 4 |
| `SPLIT-BRAIN-UNVERIFIED` | 202 |

## 1) Arithmetic (600 − 311 − 202)

- Naive row arithmetic: **87**
- Unique IDs remainder: **63**
- Duplicate-row adjustment: **24**
- Remainder IDs: `9, 15, 50, 104, 119, 120, 122, 125, 126, 127, 128, 130, 131, 132, 135, 136, 137, 138, 139, 140, 147, 151, 152, 153, 154, 155, 157, 164, 166, 172, 173, 174, 175, 176, 181, 183, 185, 186, 188, 190, 191, 193, 195, 209, 215, 224, 231, 234, 235, 236, 239, 245, 249, 250, 631, 635, 641, 704, 708, 725, 812, 814, 815`

## 2) Healthy capabilities (no integrity issue)

**Count: 4** — IDs: `338, 500, 507, 534`

## 3) Overlap WRAPPER vs SPLIT-BRAIN

- Intersection count: **0** (disjoint)

## 4) PRODUCTION-ALIGNED (Option A)

`338, 500, 507, 534`

## 5) Extension pending (CAP646)

IDs: `704, 708, 812, 814, 815`

Present in CAP978 catalog and batch-01 evidence but absent from cap646.backend_registry (binding_for raises KeyError). Require cap646 registration or dedicated CAP978-only verification path — not closed under cap646 program until registered.

**Path:** Register in cap646 catalog + backend_registry OR run separate CAP978 extension closure track

## 6) Unverified VERIFIED-DEEP / REUSED-LINK remaining

**Count: 0**

## pytest -m "not slow"

`2189 passed, 2 skipped, 4 deselected, 9739 warnings in 172.85s (0:02:52)`

