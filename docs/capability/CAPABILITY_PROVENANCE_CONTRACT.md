# Capability Provenance Contract (B1-R)

Authoritative machine-readable contract: `CAPABILITY_PROVENANCE_CONTRACT.json`.

## Purpose

Separate capability provenance into non-overloaded concepts. Historical SSOT values are preserved; this contract governs **future writes only**.

## Provenance concepts

| Concept | Canonical field(s) | Meaning |
|--------|-------------------|---------|
| Artifact composition | `git.current_head_sha`, `generated_at`, `semantic_correction.head_sha` | SSOT/metadata composed or aligned at a commit without claiming new per-cap verification |
| Actual verification | `tested_source_sha` | Commit where documented verification/test execution occurred for the capability |
| Status-change verification | `status_change.tested_sha`, `status_change.verification` | Verification event bound to an engineering-status transition |
| Validated-through | *NOT_USED in B1-R* | No separate writable field |
| Evidence generation | `semantic_correction.prior_artifact_sha`, artifact `git.tested_sha` | Artifact/evidence bundle lineage, not per-cap test execution |

## `tested_source_sha` — single canonical meaning

**Actual verification provenance only.**

A capability record may set `tested_source_sha` only when `capability_provenance.writers.record_verification_event` records a successful verification event at that commit. Artifact generation, HEAD alignment, semantic correction, and live-applicability correction must not write this field.

## Legacy policy

- Do not bulk-restamp the 932 historical capability records.
- Do not retroactively claim legacy values were actual test SHAs without evidence.
- Ambiguous pre-B1-R values remain valid as stored; classifiers may label them `LEGACY_AMBIGUOUS_PRE_B1_R` without mutation.

## Writers

All future mutations must use `capability_provenance.writers`:

- `record_artifact_composition(ssot, head_sha, generated_at)`
- `record_verification_event(cap, event, status_change_extra=...)`
- `record_semantic_correction(cap, ...)`
- `record_live_applicability_correction(cap, ...)`

Direct assignment to `tested_source_sha` outside this module is prohibited for new code paths.
