# Run 021 — ASVS 5.0 + SP 800-218A Re-Audit (Batches 01–13)

**Generated:** 2026-09-11T20:22:03.509605+00:00

## Verdict

**NEW_GAPS_IDENTIFIED** — re-audit of closed batches 01–13 under updated standards.

## Summary

| Metric | Count |
|---|---|
| Phase status deltas (legacy vs v6) | 676 |
| ASVS 5.0 new-requirement gaps (V1.14.2, V4.1.1, V8.2.1, V14.2.1, V15.1.1) | 0 |
| NIST SP 800-218A complement gaps (AI caps) | 26 |
| Phase 1 generic-delegate gate (new, not in legacy) | 494 |

## Interpretation

- **ASVS 5.0:** 0 capabilities fail ASVS 5.0 checks (V1.14.2, V4.1.1, V8.2.1, V14.2.1, V15.1.1) not present in legacy Phase 6
- **SP 800-218A:** 26 AI capabilities have 800-218A complement gaps beyond legacy AI RMF footer check
- **Generic delegate:** 494 capabilities would fail new Phase 1 generic-delegate gate (mapped to NOT_COMPLETE, not Type A reopen)
- **Closure impact:** No batch 01–12 wholesale reopen — new findings are PARTIAL/NOT_COMPLETE pathway or documented structural debt; tri-state closure counts unchanged for Type A

## Per-batch

### Batch 01 (1–50)
- Phase 6: legacy {'PARTIAL': 50} → v6 {'PASS': 47, 'PARTIAL': 3}
- Phase 3: legacy {'NOT_APPLICABLE': 49, 'PARTIAL': 1} → v6 {'NOT_APPLICABLE': 49, 'PARTIAL': 1}
- ASVS 5.0 new gaps: 0 | 800-218A gaps: 1 | generic-delegate: 0

### Batch 02 (51–100)
- Phase 6: legacy {'PARTIAL': 50} → v6 {'PASS': 49, 'PARTIAL': 1}
- Phase 3: legacy {'NOT_APPLICABLE': 49, 'PARTIAL': 1} → v6 {'NOT_APPLICABLE': 49, 'PARTIAL': 1}
- ASVS 5.0 new gaps: 0 | 800-218A gaps: 1 | generic-delegate: 0

### Batch 03 (101–150)
- Phase 6: legacy {'PARTIAL': 50} → v6 {'PASS': 49, 'PARTIAL': 1}
- Phase 3: legacy {'PARTIAL': 4, 'NOT_APPLICABLE': 46} → v6 {'PARTIAL': 4, 'NOT_APPLICABLE': 46}
- ASVS 5.0 new gaps: 0 | 800-218A gaps: 4 | generic-delegate: 0

### Batch 04 (151–200)
- Phase 6: legacy {'PARTIAL': 50} → v6 {'PASS': 49, 'PARTIAL': 1}
- Phase 3: legacy {'NOT_APPLICABLE': 45, 'PARTIAL': 5} → v6 {'NOT_APPLICABLE': 45, 'PARTIAL': 5}
- ASVS 5.0 new gaps: 0 | 800-218A gaps: 5 | generic-delegate: 49

### Batch 05 (201–250)
- Phase 6: legacy {'PARTIAL': 50} → v6 {'PASS': 48, 'PARTIAL': 2}
- Phase 3: legacy {'NOT_APPLICABLE': 47, 'PARTIAL': 3} → v6 {'NOT_APPLICABLE': 47, 'PARTIAL': 3}
- ASVS 5.0 new gaps: 0 | 800-218A gaps: 3 | generic-delegate: 50

### Batch 06 (251–300)
- Phase 6: legacy {'PARTIAL': 50} → v6 {'PASS': 50}
- Phase 3: legacy {'NOT_APPLICABLE': 49, 'PARTIAL': 1} → v6 {'NOT_APPLICABLE': 49, 'PARTIAL': 1}
- ASVS 5.0 new gaps: 0 | 800-218A gaps: 1 | generic-delegate: 50

### Batch 07 (301–350)
- Phase 6: legacy {'PARTIAL': 50} → v6 {'PASS': 49, 'PARTIAL': 1}
- Phase 3: legacy {'NOT_APPLICABLE': 50} → v6 {'NOT_APPLICABLE': 50}
- ASVS 5.0 new gaps: 0 | 800-218A gaps: 0 | generic-delegate: 50

### Batch 08 (351–400)
- Phase 6: legacy {'PARTIAL': 50} → v6 {'PASS': 50}
- Phase 3: legacy {'NOT_APPLICABLE': 49, 'PARTIAL': 1} → v6 {'NOT_APPLICABLE': 49, 'PARTIAL': 1}
- ASVS 5.0 new gaps: 0 | 800-218A gaps: 1 | generic-delegate: 50

### Batch 09 (401–450)
- Phase 6: legacy {'PARTIAL': 50} → v6 {'PASS': 50}
- Phase 3: legacy {'NOT_APPLICABLE': 48, 'PARTIAL': 2} → v6 {'NOT_APPLICABLE': 48, 'PARTIAL': 2}
- ASVS 5.0 new gaps: 0 | 800-218A gaps: 2 | generic-delegate: 50

### Batch 10 (451–500)
- Phase 6: legacy {'PARTIAL': 50} → v6 {'PASS': 49, 'PARTIAL': 1}
- Phase 3: legacy {'NOT_APPLICABLE': 50} → v6 {'NOT_APPLICABLE': 50}
- ASVS 5.0 new gaps: 0 | 800-218A gaps: 0 | generic-delegate: 50

### Batch 11 (501–550)
- Phase 6: legacy {'PARTIAL': 50} → v6 {'PASS': 48, 'PARTIAL': 2}
- Phase 3: legacy {'NOT_APPLICABLE': 49, 'PARTIAL': 1} → v6 {'NOT_APPLICABLE': 49, 'PARTIAL': 1}
- ASVS 5.0 new gaps: 0 | 800-218A gaps: 1 | generic-delegate: 50

### Batch 12 (551–600)
- Phase 6: legacy {'PARTIAL': 50} → v6 {'PASS': 49, 'PARTIAL': 1}
- Phase 3: legacy {'NOT_APPLICABLE': 48, 'PARTIAL': 2} → v6 {'NOT_APPLICABLE': 48, 'PARTIAL': 2}
- ASVS 5.0 new gaps: 0 | 800-218A gaps: 2 | generic-delegate: 49

### Batch 13 (601–650)
- Phase 6: legacy {'PARTIAL': 50} → v6 {'PASS': 44, 'PARTIAL': 6}
- Phase 3: legacy {'NOT_APPLICABLE': 45, 'PARTIAL': 5} → v6 {'NOT_APPLICABLE': 45, 'PARTIAL': 5}
- ASVS 5.0 new gaps: 0 | 800-218A gaps: 5 | generic-delegate: 46

