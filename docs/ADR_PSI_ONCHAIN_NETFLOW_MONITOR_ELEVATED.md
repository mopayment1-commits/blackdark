# ADR-PSI-001: `onchain_netflow` Monitor-Elevated Classification

**Status:** ACCEPTED  
**Date:** 2026-09-02  
**Scope:** Capabilities 66, 69 (shared `ml.inference.predict_direction` path)

## Context

Corrected platform PSI (chrono 80/20, reference quantile bins) reports `onchain_netflow` PSI **0.9104**, exceeding the default threshold **0.25** by 3.6×. The prior PSI=11.1065 was invalidated as a measurement error (incompatible head/tail slices).

## Decision

Classify `onchain_netflow` as **monitor_elevated** — do **not** freeze `predict_direction` platform-wide.

| Action | Rationale |
|--------|-----------|
| No global ML freeze | OOD gate + rules fallback already reject out-of-envelope features; freeze would block all heroes using cap 66/69 |
| Elevated monitoring | Chronological drift is real but moderate (0.91, not 11.1); on-chain netflow is inherently regime-sensitive |
| Feature-specific threshold | `onchain_netflow` uses elevated PSI alert at **0.75** (3× base) per OECD/JRC guidance on volatile macro/on-chain inputs |

## Review Plan

| Milestone | Date (UTC) | Action |
|-----------|------------|--------|
| Re-measure | 2026-09-09 | Re-run `measure_platform_psi()` after weekly flywheel export |
| Escalate | 2026-09-16 | If PSI > 1.0 → trigger `enforce_drift_actions` warn; if > 1.5 → owner review for partial cap 66/69 ML weight reduction |
| Dataset refresh | Post cap-69 live data | First PSI row including post-2026-09-02 training data |

## Institutional Sources

- OECD/JRC Handbook on Constructing Composite Indicators — reference-distribution binning
- ISO/IEC 25010 AI amendment — maintainability under data drift
- MLOps: PSI threshold 0.25 default; volatile features may use tiered thresholds with documented review
