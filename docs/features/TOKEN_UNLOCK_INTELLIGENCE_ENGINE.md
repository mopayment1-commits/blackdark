# Token Unlock Intelligence Engine — #703 + #704 + #707 + #708 (Sprint 2)

Unified unlock engine: Calendar + Impact Score + Actionability + Dashboard.

| Ticket | Role |
|--------|------|
| #707 | Unlock Impact Intelligence (primary engine) |
| #703 | Actionability Score (absorbed into impact composite) |
| #704 | Token Unlock Calendar (absorbed into #708 dashboard) |
| #708 | Dashboard (Calendar + List + Magnitude + Impact + Actionability) |

## Key Rules

| Rule | Implementation |
|------|----------------|
| Formula documented | `formula_version: 1.0` on every score |
| No guaranteed direction | `no_guaranteed_price_direction: true` |
| Historical calibration | Similar unlocks declined 60% of time (backtest, not prediction) |
| Unlock ≠ sell signal | `unlock_not_automatic_sell_signal: true` |
| Primary sources | `primary_source_url` + `assumptions` stored |
| Revisions tracked | `revision_history` array |
| Missing unlock | `missing_unlock_treated_as_zero: false` |

## Scores

**Impact Score (0–100):** magnitude + liquidity absorption + recipient weight + historical similarity

**Actionability Score (0–100):** impact + USD size + liquidity gap + exchange flows + volatility + sentiment, with `reasons` and `conflicting_factors`

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/intelligence-ledger/token-unlock/status` | Engine status |
| `GET /api/platform/intelligence-ledger/token-unlock/dashboard` | #708 full dashboard |
| `GET /api/platform/intelligence-ledger/token-unlock/calendar` | #704 calendar (absorbed) |
| `GET /api/platform/intelligence-ledger/token-unlock/impact` | #707 impact panel |
| `GET /api/platform/intelligence-ledger/token-unlock/actionability` | #703 actionability (absorbed) |

## Disclaimer

Unlock event ≠ automatic sell signal. Scores describe contextual impact — not trade signals.
