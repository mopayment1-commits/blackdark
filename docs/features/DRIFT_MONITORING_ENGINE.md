# Drift Monitoring Engine — #209 + #213 (merged)

Sprint 0/1 — Drift Monitoring Engine merging #209 Drift Detection and #213 Market/Data Drift Monitoring.

Extends `ml/drift_monitor.py` with platform-level market/data drift monitoring.

## Institutional Rules

| Rule | Implementation |
|------|----------------|
| Versioned baselines | `Baseline v2.1 \| Window: 30 days \| Updated: YYYY-MM-DD` |
| False-alarm review | Every alert reviewed before action (`review_drift_alert`) |
| Data gap ≠ drift | `Data Gap` and `Stale Data` separated from `Distribution Drift` |
| Reproducible tests | Deterministic PSI — same input → same checksum |
| No auto promotion | `no_automatic_promotion: true`, human review required |
| Severity + persistence | Low/1h, Medium/1d, High/1week |
| Retraining trigger | `Recommended: Review \| Not: Auto-retrain` |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/drift-monitoring/status` | Module status + policies |
| `GET /api/platform/drift-monitoring/baselines` | Versioned baselines list |
| `GET /api/platform/drift-monitoring/baselines/{version}` | Baseline detail |
| `GET /api/platform/drift-monitoring/dashboard` | Drift dashboard (current + stale samples) |
| `POST /api/platform/drift-monitoring/detect` | Run drift detection on values |
| `POST /api/platform/drift-monitoring/review` | False-alarm review |
| `POST /api/platform/drift-monitoring/reproducible-test` | Deterministic reproducibility test |

## Related

- `ml/drift_monitor.py` — ML model drift (PSI, OOD, freeze trading)
- `bd_platform/source_registry_provenance.py` — data lineage and audit
