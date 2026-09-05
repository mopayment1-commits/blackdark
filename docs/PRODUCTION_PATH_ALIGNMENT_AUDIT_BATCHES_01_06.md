# Production path alignment audit — batches 01–06

**Generated:** 2026-08-31T07:30:45.397009+00:00
**Assessed:** 202 capabilities (VERIFIED-DEEP + REUSED-LINK)

## Summary

| Status | Count | Meaning |
|--------|------:|---------|
| `SPLIT_BRAIN_GENERIC_HANDLER` | 3 | Production uses track/keyword generic handler |
| `SPLIT_BRAIN_OTHER` | 10 | Other mismatch |
| `SPLIT_BRAIN_REUSED` | 45 | REUSED-LINK with mismatched paths |
| `SPLIT_BRAIN_ROUTING` | 144 | pdf_registry binding ≠ production backend_registry |

## Non-aligned IDs

### SPLIT_BRAIN_GENERIC_HANDLER (3)

25, 46, 299

### SPLIT_BRAIN_OTHER (10)

1, 10, 11, 14, 17, 36, 55, 330, 382, 629

### SPLIT_BRAIN_REUSED (45)

3, 4, 5, 6, 7, 12, 13, 19, 20, 21, 22, 27, 28, 29, 30, 33, 34, 37, 40, 44, 45, 47, 48, 56, 62, 111, 214, 279, 339, 356, 379, 390, 437, 441, 458, 525, 578, 584, 637, 638, 639, 640, 642, 644, 645

### SPLIT_BRAIN_ROUTING (144)

2, 18, 49, 59, 60, 63, 69, 71, 72, 73, 74, 75, 77, 79, 81, 85, 86, 88, 91, 92, 96, 98, 101, 102, 103, 105, 106, 107, 108, 109, 110, 112, 113, 114, 115, 116, 117, 118, 121, 123, 124, 129, 133, 134, 141, 142, 143, 144, 145, 146
... +94 more (see JSON)

