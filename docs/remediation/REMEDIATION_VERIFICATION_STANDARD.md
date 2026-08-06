# Remediation Verification Standard
**Version:** 3.0 | **Date:** 2026-08-05

## Lifecycle States (allowed only)
OPEN → IN_REMEDIATION → REMEDIATED_PENDING_IVV → VERIFIED_CLOSED

## Forbidden States
ACCEPTED_RISK, WAIVED, DOCUMENTED_ONLY, PARTIALLY_CLOSED

## Terminal Outcome
**ROOT REMEDIATION 42/42 VERIFIED CLOSED** requires:
- 42/42 parent findings VERIFIED_CLOSED
- 29/29 sub-findings VERIFIED_CLOSED
- all other lifecycle counts = 0
- regressions = 0; replacement defects = 0
- authority conflicts = 0; data-authority conflicts = 0; execution-authority conflicts = 0
- migration deficiencies = 0; test-contract deficiencies = 0; preventive-control deficiencies = 0
- non-reproducible evidence = 0

## IVV Process
1. Implementer marks REMEDIATED_PENDING_IVV with evidence artifact hash
2. Independent IVV reruns test matrix cells marked REQUIRED for the step
3. IVV signs E-IVV/{step}-signoff.json
4. Program Owner updates REMEDIATION_PROGRAM_STATE.md

## ssot-doc-lint Contract (Implementable)

| Field | Specification |
|-------|---------------|
| Script | `scripts/ssot_doc_lint.py` |
| Scanned files | `docs/**/*.md`, `docs/institutional/**/*.md`, `FEATURE_REALITY_MATRIX.md`, `WAVE2_MASTER_REFERENCE_INDEX.md` |
| Allowed authority | Exactly one `status: CURRENT_SSOT` declaration per authority class (feature, price, execution, platform) linked from `docs/institutional/CURRENT_PROGRAM_STATUS_POINTER.md` |
| Forbidden | Duplicate CURRENT_SSOT; LIVE marker on HISTORICAL_NON_CURRENT; enumeration claims in audit matrices; F-### IDs emitted from bd_platform/registry.py docs |
| Failure messages | `DUPLICATE_SSOT_AUTHORITY:{file}:{class}`; `STALE_LIVE_MARKER:{file}`; `FORBIDDEN_ENUMERATION:{file}` |
| CI integration | `.github/workflows/ci.yml` job `ssot-doc-lint` after checkout, before test job |
| Tests | `tests/governance/test_ssot_doc_lint.py` — fixture docs with intentional violations must fail lint |
| Evidence output | `E-GOV/ssot-lint-report.json` with scanned count, violations[], sha256 |
| Blocking | PR merge blocked on any violation |

## Test Matrix Validation
Each of 2286 cells (127 steps × 18 classes) must be REQUIRED with 5 subfields or NOT_APPLICABLE_WITH_REASON with step-specific reason. No R/NA shorthand.

## Migration Validation
MIG-01 through MIG-07 each require 21 fields and IVV signoff. MIG-03 must retire REAL columns. MIG-05 requires MIG-03 rollback boundary. MIG-06 requires zero legacy callers (90-day alone insufficient). MIG-07 proves single audit authority. No permanent dual-read/write/authority.
