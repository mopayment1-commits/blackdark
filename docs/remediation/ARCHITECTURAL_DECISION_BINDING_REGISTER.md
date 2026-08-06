# Architectural Decision Binding Register
**Version:** 3.0 | **Date:** 2026-08-05 | **Status:** ACTIVE

## DEC-A — Feature Enumeration Authority
- **Decision:** Owner-approved FCP master list is sole feature enumeration authority.
- **Binding:** Features are imported/attested, not CAP-derived. F-001 and F-002 are immutable.
- **Blocked until:** R0-S01 attestation (NOT AUTHORIZED to execute).
- **Evidence:** E-GOV/DEC-A-binding.json
- **Preventive control:** ssot-doc-lint FORBIDDEN_ENUMERATION; tests/test_registry_not_enumeration_authority.py

## DEC-B — Feature↔CAP Mapping
- **Decision:** Many-to-many mapping; exactly one primary CAP per feature.
- **Binding:** Crosswalk document blocked until DEC-A attestation closes.
- **Evidence:** E-GOV/DEC-B-crosswalk.json
- **Preventive control:** tests/test_feature_cap_crosswalk.py (future)

## DEC-C — Price Truth (Data Authority)
- **Decision:** Public API: `market_context.get_canonical_price()` / `get_canonical_venue_price()`. Internal: `unified_global_price.compute_ugp()`. Substrate: `live_book_hub`. REST/stale prices cannot authorize execution.
- **Repository evidence:** `live_book_hub.py` exists; canonical APIs and `unified_global_price.py` absent (PC-004).
- **Remediation:** R2-S03, R2-S04, MIG-02
- **Preventive control:** tests/contract/test_price_authority.py; execution auth rejects non-canonical sources

## DEC-D — Execution Authorization
- **Decision:** `EXECUTION_ENABLED` master switch via `execution_safety_guard`. Conflict/UNKNOWN=DENY. Persisted safety state required.
- **Repository evidence:** `AUTO_EXECUTION_ENABLED` in execution_engine.py; `execution_safety_guard.py` absent (PC-005).
- **Remediation:** R3-S01, R3-S02, MIG-04
- **Preventive control:** tests/security/test_execution_safety_guard.py; fail-closed at startup

## DEC-E — Platform Semantics (P01–P16)
- **Decision:** Modular monolith platforms P01–P16. No P17. No premature microservice extraction.
- **Repository evidence:** `microservices/` present (PC-031 tension).
- **Remediation:** R4-S13
- **Preventive control:** tests/arch/test_no_p17_platform.py; architecture test for monolith boundaries

## R0-S10 — Navigation Index Rule
- **Decision:** WAVE2_MASTER_REFERENCE_INDEX.md is navigation-only; cannot declare authority.
- **Preventive control:** ssot-doc-lint STALE_LIVE_MARKER and FORBIDDEN_ENUMERATION rules
- **Step:** R0-S10

## Owner Decision Register (R0-S01)
| OD ID | Description | Input | Output |
|-------|-------------|-------|--------|
| OD-01 | Feature enumeration authority attestation | Signed owner letter | FEATURE_REGISTRY_ATTESTATION.md |
| OD-02 | F-001/F-002 immutability confirmation | Owner sign-off | Attestation section F-001/F-002 |
| OD-04 | Attestation format approval | Legal/compliance review | Approved template ID |

**R0-S01 Execution Authorized:** NO
