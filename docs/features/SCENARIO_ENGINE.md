# Scenario Engine — #751 (Sprint 2, Enterprise tier)

Probabilistic scenarios — **NOT** deterministic prediction.

Transforms future into testable probability-weighted scenarios with calibration,
sensitivity analysis, and invalidation conditions.

## Institutional Rules

| Rule | Implementation |
|------|----------------|
| Calibration tested | `Calibration tested on 2023-2025 data \| Brier Score: 0.182` |
| Probabilities sum coherently | `Scenario A: 30% \| B: 45% \| C: 25% \| Sum: 100%` |
| No certainty language | "Likely" / "Probability: X%" — never "Will" / "Prediction" |
| Assumptions versioned | `Assumptions: ... \| Version: 2.1 \| Date: YYYY-MM-DD` |
| Invalidation conditions | `This scenario invalidates if: BTC breaks $X` |
| Sensitivity analysis | `If Fed cuts 25bps → Probability shifts: A +5% \| B -3% \| C -2%` |
| Disclaimer | Mandatory, non-hideable |
| Tier | Enterprise (Institutional) only |

## APIs

| Endpoint | Tier | Description |
|----------|------|-------------|
| `GET /api/platform/scenario-engine/status` | All | Module status |
| `GET /api/platform/scenario-engine/calibration` | All | Calibration metadata |
| `GET /api/platform/scenario-engine?asset=BTC` | Enterprise | Generate scenario set |
| `GET /api/platform/scenario-engine/sensitivity?shock=...` | Enterprise | Sensitivity analysis |

## Related

- `oracle_scenarios.py` — lightweight Oracle fan-out (not institutional Scenario Engine)
- `bd_platform/portfolio_risk_analytics.py` — portfolio risk simulation (#746)
