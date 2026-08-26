# Historical Narrative Explorer — #250

## Institutional Decision

Renamed from **Historical Crypto Trends** → **Historical Narrative Explorer** (Sprint 2 Intelligence Layer).

Answers **"what happened?"** not **"what will happen?"** — legally safe, institutionally valuable.

Complements: **#758 Trending Words** + **#293 Real-time Alerts**  
Integrates with: **#756 Thesis Workspace**

Sentiment research only — no yield/arbitrage alerts.

## Mandatory Rules

| Rule | Implementation |
|------|----------------|
| No causation claim | `Correlation ≠ Causation` on every view |
| Timestamps aligned | UTC hourly alignment verified |
| Historical data preserved | Dataset versioned, no overwrite |
| Lead/lag documented | xcorr, ±30 days, 90D rolling, p<0.05 |
| Narrative extraction transparent | TF-IDF + manual curation, spam/bot filtered |
| Correlation descriptive | No buy signals |
| Explorer UX | User explores, doesn't receive answers |
| No opportunity alerts | Buy-signal alerts forbidden |
| Disclaimer non-hideable | Always visible |

## Example Output

```
Correlation: 0.65 | Lead/Lag: Narrative leads price by 3 days | Note: Correlation ≠ Causation
Narrative peak: 2024-03-15 14:00 UTC | Price peak: 2024-03-18 09:00 UTC | Lag: +67 hours
Dataset v3.1 | Social: X API v2 | Price: Oracle API | Coverage: 2020-01-01 to 2026-08-25
```

## API

```
GET /api/platform/intelligence-ledger/intelligence-layer/historical-narratives/status
GET /api/platform/intelligence-ledger/intelligence-layer/historical-narratives?narrative_id=defi_summer&asset=ETH
GET /api/platform/intelligence-ledger/intelligence-layer/historical-narratives/historical-qa
```

## Layer Architecture

```
Intelligence Layer (Sprint 2)
├── #758 Trending Words (current)
├── #293 Real-time Alerts (detection)
└── #250 Historical Narrative Explorer (archive)
    └── integrates → #756 Thesis Workspace
```
