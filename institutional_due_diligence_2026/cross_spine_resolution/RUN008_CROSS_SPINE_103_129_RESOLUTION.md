# Run 008 — Cross-Spine Resolution (IDs 103, 129)

**Generated:** 2026-09-11T08:07:55.769959+00:00  
**Run:** Master Contract 008  
**Scope:** CROSS-SPINE-001 remediation before Batch03 opening  

## Closure Gate (Run 008)

| Criterion | Status |
|---|---|
| 103/129 routing updated + documented | **MET ✅** |
| Batch01 non-regression (`closure_gate.met`) | **MET ✅** |
| Batch02 non-regression (`closure_gate.met`) | **MET ✅** |
| Zero unknown BATCH0X routing overlaps | **MET ✅** (0) |

## Item 1 — Diagnosis (Run 007 methodology)

### Literal list membership (post-fix)

```python
LEGACY_BATCH01_EXTENSION_IDS = [175, 214, 245, 584, 629, 630, 631, 642, 644, 646]
BATCH03_IDS = range(101, 151)  # includes 103, 129
runtime order: BATCH01_IDS → BATCH02_IDS → BATCH03_IDS
```

### Pre-fix state (Run 008 diagnosis, before code change)

| ID | LEGACY | BATCH01_IDS | BATCH03_IDS | production_spine | backend_module | success |
|---:|:---:|:---:|:---:|---|---|---|
| 103 | ✅ | ✅ | ✅ | **batch01** | cap646.batch01_production | true |
| 129 | ✅ | ✅ | ✅ | **batch01** | cap646.batch01_production | true |

Runtime checked `BATCH01_IDS` first → misrouted to batch01 legacy handlers (`institutional` #103, `market` #129) despite official batch03 range.

### Post-fix state (live)

| ID | in BATCH01_IDS | in BATCH03_IDS | batch01_direct | batch03_direct | routing |
|---:|:---:|:---:|---|---|---|
| 103 | False | True | ValueError: capability 103 is not in bat | ValueError: capability 103 is official batch03 — d | batch03_spine_reached |
| 129 | False | True | ValueError: capability 129 is not in bat | ValueError: capability 129 is official batch03 — d | batch03_spine_reached |

## Item 2 — Decision Source

**Verdict:** Scope-expansion error — legacy cherry-pick, not official batch01.

**Primary sources:**
1. `docs/HERO_BATCH_TRANSPARENCY.md` — prior BATCH01 cherry-pick (including 103) preserved as `LEGACY_BATCH01_EXTENSION_IDS` for spine compatibility; **not official batch01 closure**.
2. Official 826 batch ranges: batch03 = **101–150** (103 = API Data Platform, 129 = Sentiment Intelligence).
3. Same structural pattern as Run 007 IDs 55/56/59/60 (legacy extension vs official batch range).

**Action taken (Run 008):**
- Removed 103, 129 from `LEGACY_BATCH01_EXTENSION_IDS` and batch01 handler maps.
- Registered as `BATCH03_PENDING_DEDICATED_IDS` — batch03 spine routing only; dedicated handlers deferred to Batch03 audit.

## Item 3 — Non-Regression

| Batch | closure_gate.met | CONCEPTUALLY-UNSOUND | Script |
|---|---:|---:|---|
| Batch01 | True | 0 | run005_batch01_final_closure.py |
| Batch02 | True | 0 | run007_batch02_final_closure.py |

## Item 4 — Final Overlap Scan

- **Routing overlaps (BATCH01∩BATCH02∩BATCH03):** 0
- **batch04+ production modules in cap646/:** none (grep exit 1)
- **Full overlap list:** `[]`

## Batch03 Opening

**NOT opened in this run.** Batch03 audit remains a separate Master Contract after Run 008 gate confirmation.
