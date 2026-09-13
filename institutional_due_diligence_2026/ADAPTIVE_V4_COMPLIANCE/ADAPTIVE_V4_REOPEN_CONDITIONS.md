# Adaptive v4 Local Completion — Reopen Conditions

The accepted local-completion state registered at baseline SHA `07bb4049` is **invalidated or reopened** when any of the following material conditions occur. After reopening, `ADAPTIVE_V4_FINAL_LOCAL_COMPLETION` must be re-established through full gate verification.

## Material Changes That Reopen Local Completion

### 1. Adaptive Production Code

Any change to Adaptive production code under verified paths that affects behavior covered by the institutional evidence package, including but not limited to:

- `bd_platform/adaptive_intelligence/`
- `api/routers/adaptive_intelligence.py`
- `governance/adaptive_ux_requirements.py`

### 2. Router / Decision Contract / Confidence / Boundary Semantics

Changes to:

- Intelligence router stage ordering, abstention logic, or observability contracts
- Decision contract structure, stance derivation, or confidence vector semantics
- Decision boundary thresholds or false-precision rules
- Uncalibrated numeric confidence presentation rules

### 3. Entitlement Authority

Changes that weaken, bypass, or relocate entitlement authority for Adaptive capabilities, including `entitlement_gate.py` and cap646 integration paths.

### 4. Evidence Classes and Provenance

Changes to evidence-class semantics, provenance rules, or requirement extraction that alter the normative obligation set or its traceability.

### 5. Trust Dimensions

Changes to trust dimension definitions, weighting, or integrity constraints in `trust_dimensions.py` and dependent surfaces.

### 6. Security Controls

Changes to Adaptive attack-surface controls in `security_controls.py` or security-relevant API validation that reduce coverage verified in `ADAPTIVE_V4_SECURITY_VERIFICATION_MATRIX.json`.

### 7. User-Facing Adaptive Interaction (Accessibility)

Changes to user-facing Adaptive HTML/templates, keyboard interaction paths, focus management, or disclosure surfaces that require accessibility re-validation.

### 8. Schema / Persistence

Schema or persistence changes affecting Adaptive data models, decision history, or audit trails relied upon by verified behavior.

### 9. Canonical Dependency Changes

Changes to canonical dependencies (auth middleware, cap646 entitlement engine, dashboard routing, shared governance modules) that invalidate regression assumptions in `ADAPTIVE_V4_REGRESSION_IMPACT_MATRIX.json`.

### 10. Requirement / Specification Change

Any change to the authoritative specification file or normative requirement count that adds, removes, or reclassifies obligations without updated atomic mapping and provenance reconciliation.

## Changes That Do NOT Automatically Reopen

The following do **not** by themselves invalidate local completion:

- Non-material documentation updates (README, comments, institutional narrative) that do not alter verified behavior or evidence semantics
- Unrelated repository changes outside Adaptive verified scope
- Regeneration of gate-runner ephemeral artifacts with unchanged semantic outcomes
- External-gate evidence collection (production SLO, calibration studies, human validation) — these remain gated independently

## Re-Verification Procedure

When a reopen condition is triggered:

1. Implement or remediate the material change
2. Re-run `python3 scripts/adaptive_v4_gate_runner.py`
3. Confirm `BASELINE_INTEGRITY_VERIFIED=true` and `ADAPTIVE_V4_FINAL_LOCAL_COMPLETION=true`
4. Update `ADAPTIVE_V4_FINAL_LOCAL_BASELINE.json` and `ADAPTIVE_V4_EVIDENCE_MANIFEST.json` only if establishing a new accepted baseline (do not silently mutate the frozen `07bb4049` record)
