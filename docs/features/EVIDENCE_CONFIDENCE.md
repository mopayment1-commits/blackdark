# Evidence Confidence Framework — #284 (Sprint 2 Intelligence Ledger)

Cross-cutting evidence-quality scoring for research outputs.

**NOT** probability of price move. **NOT** profit probability.

## Formula (public, versioned)

```
confidence = (source_quality×0.30 + recency×0.20 + agreement×0.20
            + methodology×0.15 + completeness×0.15) × (1 - contradiction_penalty)
```

| Component | Weight |
|-----------|--------|
| Source quality | 30% |
| Recency | 20% |
| Agreement | 20% |
| Methodology | 15% |
| Completeness | 15% |

## Institutional Rules

| Rule | Implementation |
|------|----------------|
| Not probability | UI: "Confidence in evidence quality" |
| Contradiction penalty | Majority or expert-weighted resolution |
| Calibration | Monthly FP/FN tracking |
| Reproducible | Same inputs → same score |
| No black-box | Formula public + versioned |

## Disclaimer

"This score measures evidence strength, not investment outcome."

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/intelligence-ledger/evidence-confidence/status` | Framework status |
| `GET /api/platform/intelligence-ledger/evidence-confidence` | Assessment with breakdown |
