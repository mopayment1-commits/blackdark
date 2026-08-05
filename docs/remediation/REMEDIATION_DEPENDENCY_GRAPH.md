# Remediation Dependency Graph
**Version:** 3.0 | **Acyclic:** YES

```
R0-S01 → R0-S02 (attestation before pointer doc)
R0-S02 → R0-S03 (pointer before institutional scaffold)
R0-S05 → R0-S06 (taxonomy before ssot-doc-lint)
R0-S06 → R0-S10 (lint before wave index)
R0 complete → G0 → R1-S01
R1-S01 → R1-S02 (env baseline before Python pin ONLY)
R1-S02 → R1-S03 (Python pin before dependency audit)
R1-S04 → R1-S05 (audit before FULL test-suite CI gate ONLY)
R1-S07 → MIG-01 → R1-S08
R1 complete → G1 → R2-S01
R2-S03 → MIG-02 → R2-S04
R2-S05 → MIG-03 → R2-S06 (MIG-03 rollback boundary before MIG-05)
MIG-03 verified rollback → MIG-05 → R2-S12
R2 complete → G2 → R3-S01
R3-S03 → R3-S08 → MIG-04 (config gate before persistence)
R3 complete → G3 → R4-S01
R4-S02 → R4-S04 (import lint before registry retirement)
R4-S10 → R4-S14 (startup opt-in before compliance centralization)
R4 complete → G4 → R5-S01
R5-S08 → MIG-06 (zero legacy callers + prohibited-import)
R5-S11 → MIG-07 (single audit authority)
R5 complete → G5 → R6-S01
R6 complete → G6 → R7-S01
R7-S01 BEFORE shared test infrastructure changes (R7-S02+)
R3/R4 configuration-startup integration gate: R4-S03 ‖ R3-S03 only after R3-S02
R5 and R6 SEQUENTIAL — no parallel (shared auth_service.py, production_guard.py)
R7 complete → G7 → R8-S01
R8 AFTER R7 evidence closure
R8-S12 → ROOT REMEDIATION 42/42 VERIFIED CLOSED
```

## Gate Definitions

- **G0:** Stream R0 all steps VERIFIED_CLOSED before R1 if i<8 else terminal IVV
- **G1:** Stream R1 all steps VERIFIED_CLOSED before R2 if i<8 else terminal IVV
- **G2:** Stream R2 all steps VERIFIED_CLOSED before R3 if i<8 else terminal IVV
- **G3:** Stream R3 all steps VERIFIED_CLOSED before R4 if i<8 else terminal IVV
- **G4:** Stream R4 all steps VERIFIED_CLOSED before R5 if i<8 else terminal IVV
- **G5:** Stream R5 all steps VERIFIED_CLOSED before R6 if i<8 else terminal IVV
- **G6:** Stream R6 all steps VERIFIED_CLOSED before R7 if i<8 else terminal IVV
- **G7:** Stream R7 all steps VERIFIED_CLOSED before R8 if i<8 else terminal IVV
- **G8:** Stream R8 all steps VERIFIED_CLOSED before R9 if i<8 else terminal IVV
