# Macro Context Engine — Features #141 + #104 (Sprint 2)

## Role

Relationship-based macro context — **not raw data lists**.

Merged with TwelveData (#104) into a single engine feeding Oracle (#125).

## Output Format

```
DXY rose 1.2% → historically BTC drops ~3% → expected impact: negative
```

Arabic:
```
DXY ارتفع 1.2% → تاريخياً BTC ينخفض ~3% → التأثير المتوقع: سلبي
```

## Data Sources

1. **TwelveData** (#104) — when `TWELVEDATA_API_KEY` configured
2. **Yahoo Finance** — fallback via `macro_correlations`
3. **Regime context** — Risk-On / Risk-Off / Neutral

## Oracle Integration (#125)

When a user queries an asset, the Oracle appends macro context to the single reason line when available.

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/macro/context?asset=BTC` | Relationship chains |
| `GET /api/platform/macro/context/status` | Engine health |

## Acceptance

- Query ≤ 2 seconds (target ≤1s cached)
- Accuracy ≥ 95%
- Relationships, not lists
- 2-year retention via `macro_correlations` DB logs
