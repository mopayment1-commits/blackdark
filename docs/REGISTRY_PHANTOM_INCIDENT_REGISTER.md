# Registry phantom-success incident register

**Severity:** Same class as incidents #311 (TEMPLATE-SEED-STUB) and #202 (SPLIT-BRAIN)  
**Generated:** 2026-08-31 UTC  
**Audit:** `docs/REGISTRY_PHANTOM_SUCCESS_AUDIT.json`

## Incident summary

Historical "quad-evidence" and batch closure reports used `pdf_capability_registry.execute_capability` and pytest bindings. **Production** uses `cap646.backend_registry.binding_for` → `GET /api/cap646/{id}`.

Capabilities can show **apparent success** in audit/tests while **absent from cap646 registry** (`KeyError`).

## Affected IDs (7 total — expanded from original 5)

| ID | Prior "success" context | pdf_registry | cap646 registry | Status now |
|----|-------------------------|--------------|-----------------|------------|
| **704** | Batch-01 REUSED-LINK / gap live_ok | YES | **NO** | EXTENSION-PENDING-CAP646 |
| **708** | Batch-01 sample dossier + gap live_ok | YES | **NO** | EXTENSION-PENDING-CAP646 |
| **725** | Batch-01 sample dossier (#10 random sample) | YES | **NO** | EXTENSION-PENDING-CAP646 |
| **812** | Batch-01 completion manual binding + gap | YES | **NO** | EXTENSION-PENDING-CAP646 |
| **813** | Batch-01 completion manual binding (#813 cited) | NO | **NO** | EXTENSION-PENDING-CAP646 |
| **814** | Batch-01 completion manual binding + gap | YES | **NO** | EXTENSION-PENDING-CAP646 |
| **815** | Batch-01 completion manual binding + gap | YES | **NO** | EXTENSION-PENDING-CAP646 |

## Sample audit scope

- **577** unique IDs from all `HERO_BATCH_*_SAMPLE*.json`, severity panels, and gap-report `live_ok` rows
- **7** registry phantoms (pdf ok or cited in completion report, cap646 KeyError)
- **2 newly discovered** beyond original five: **#725**, **#813**

## Other historical samples

All other sampled IDs in dossiers (e.g. severity panel 2,18,49,59,60,101,201,316,409,517) **are in cap646 catalog** but were SPLIT-BRAIN — different failure mode (registry present, wrong binding), not phantom registry.

## Required action

Same escalation track as 311/202:

1. Suspend VERIFIED-DEEP / REUSED-LINK claims on extension IDs until cap646 registration OR dedicated CAP978 extension closure
2. No batch closure credit for quad-evidence that did not use production path
3. Register + wire before any ban-lift consideration
