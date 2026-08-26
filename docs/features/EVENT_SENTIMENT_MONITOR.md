# Event & Sentiment Monitor — Feature #443

## Decision

**Sprint-2 — merged into Intelligence Ledger as "Event & Sentiment Monitor".**

Renamed from "Event-Driven Arbitrage" → **Event & Sentiment Monitor**

Execution language banned: buy, sell, automatic, exploit, short (شراء، بيع، آلي، استغلال)

| Cancelled v1 | Reason |
|--------------|--------|
| Google Trends | API limited and unreliable |
| Auto-trading / execution | Institutional decision — analytics only |
| Standalone module | Merged into Intelligence Ledger |

## Scope (monitoring only)

| Capability | Description |
|------------|-------------|
| NLP Sentiment | Twitter, Reddit, Telegram, News — 15-min refresh |
| Event Calendar | Hard forks, listings, delistings, regulatory, unlocks, migrations, mergers |
| Fear/Greed Index | Unrealized PnL + funding rates + social volume |
| Asset Scoring Metrics | MC/Volume ratio (P/E-like) + total on-chain value |
| Price Correlation | Sentiment vs price alignment |
| Alerts | Alert-only — no execution recommendations |
| Archive | ≥1 year retention |

## Acceptance Criteria

| Criterion | Target |
|-----------|--------|
| Update interval | 15 minutes |
| NLP accuracy | ≥80% |
| Source coverage | ≥5 sources |
| Archive retention | ≥1 year |

## Routes

```
GET /api/platform/intelligence-ledger/event-sentiment/status
GET /api/platform/intelligence-ledger/event-sentiment
GET /api/platform/intelligence-ledger/event-sentiment/calendar
GET /api/platform/intelligence-ledger/event-sentiment/alerts
GET /api/platform/intelligence-ledger/event-sentiment/archive
GET /api/platform/intelligence-ledger/event-sentiment/reconciliation-tests
```

## Integrations

- **#429** — `enrich_opportunity()` attaches `event_sentiment_context_443` with sentiment + event proximity
- **#287 Community Pulse** — complementary purchased-feed sentiment
- **Asset Scoring** — MC/Volume and on-chain total value metrics
