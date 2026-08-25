# Social Hype Analyzer — #293 (replaces #758, Sprint 2)

Sentiment Early Warning System — detects abnormal social interest before wide narrative formation.
Merged into #139 Sentiment Intelligence — NOT buy opportunity framing.

## Institutional Rules

| Rule | Implementation |
|------|----------------|
| Historical baseline | `30-day rolling average \| Window: 7D/30D/90D \| Last Updated` |
| Bot-adjustment | Account age 30d, min 100 followers, engagement quality /10 |
| Multi-source confirmation | Twitter + Reddit + Telegram + Discord + News |
| Alert precision measured | `82 TP \| 18 FP \| Precision: 82%` — errors not hidden |
| Three reasons per alert | Volume vs baseline, multi-source, engagement quality |
| Not opportunity | `Hype Spike Detected` — no "Buy now" language |
| No look-ahead | Data up to moment T only |
| Version documented | `Hype Analyzer v2.1 \| Rolling Median \| 3σ` |

## Output Contract

```json
{
  "hype_spike": "Detected",
  "affected_tokens": ["BTC"],
  "acceleration_pct": 476.0,
  "confidence_pct": 87.0,
  "sources_confirmed": 4,
  "sources_confirmed_display": "Sources Confirmed: 4/5",
  "alert_reasons": [
    {"reason": 1, "display": "Reason 1: Mention volume +476% above 30D baseline"},
    {"reason": 2, "display": "Reason 2: Confirmed across 3+ sources"},
    {"reason": 3, "display": "Reason 3: Engagement quality score: 8.2/10"}
  ],
  "disclaimer_hideable": false
}
```

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/market-radar/sentiment/hype/status` | Module status |
| `GET /api/platform/market-radar/sentiment/hype` | Per-asset hype analysis |
| `GET /api/platform/market-radar/sentiment/hype/scan` | Market-wide hype scan |

## Integration

- `bd_platform/sentiment_intelligence.py` — `social_hype_analyzer` block on every sentiment response
- Replaces/upgrades #758

## Related

- `bd_platform/unique_social_volume.py` — #195 bot dedup layer
- `bd_platform/weighted_social_sentiment.py` — #197 quality weighting
