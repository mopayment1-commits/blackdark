# Diligence Risk Scoring — Feature #460

Sprint-2 Risk Layer Core. Converts due diligence findings into comparable risk scores with full transparency.

## Endpoints

| Route | Description |
|-------|-------------|
| `GET /api/platform/intelligence-ledger/portfolio-ai/risk-scoring/status` | Feature status |
| `GET /api/platform/intelligence-ledger/portfolio-ai/risk-scoring` | Full risk panel |
| `GET /api/platform/intelligence-ledger/portfolio-ai/risk-scoring/entity/{id}` | Entity overall + category scores |
| `GET /api/platform/intelligence-ledger/portfolio-ai/risk-scoring/collateral/{id}` | #462 Collateral Risk |
| `GET /api/platform/intelligence-ledger/portfolio-ai/risk-scoring/correlation/{id}` | #463 Correlation Risk |
| `GET /api/platform/intelligence-ledger/portfolio-ai/risk-scoring/opportunity-ranking` | #417 Net-Edge adjusted ranking |

## Scoring model

Weighted categories (documented in seed):
- Asset diligence — 35%
- Collateral risk (#462) — 25%
- Correlation risk (#463) — 20%
- Venue diligence — 20%

Each finding contributes: `severity × evidence_confidence × freshness_factor`

## Acceptance

- **No opaque score:** breakdown + weights + version on every score
- **Evidence quality affects confidence:** low-quality sources reduce confidence automatically
- **#417 integration:** `final_rank_score = truth_score × (1 − risk_penalty) × confidence_adj`

## Shared engine

#462 Collateral Risk and #463 Correlation Risk use the same scoring engine — not separate modules.
