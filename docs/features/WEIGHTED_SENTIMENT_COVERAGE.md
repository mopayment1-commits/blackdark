# Weighted Sentiment & Connector Coverage — #197, #200

## #197 — Weighted Social Sentiment (Sentiment Quality Engine)

Layer within #139 Sentiment Engine — merged with #195.

| Requirement | Implementation |
|-------------|----------------|
| Weights explicit | `weights_version: 1.0.0` + documented source table (0.1–2.0) |
| Author activity | Accounts <7 days → 0.2× weight |
| Manipulation resistance | 100-bot injection test — delta must stay ≤0.08 |
| Explain contributors | "Positive sentiment 70% (driven by CoinDesk, Analyst_A, Whale_Alert)" |

### APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/sentiment/quality?asset=BTC` | Full quality report |
| `GET /api/platform/sentiment/quality/status` | Engine status |
| `POST /api/platform/sentiment/quality/manipulation-test` | Run bot-wave test |

Integrated into `analyze_asset_sentiment()` as `sentiment_quality` block.

---

## #200 — API Coverage Registry (part of #194)

**Not a separate product** — documentation endpoint on Unified Connector.

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/coverage` | Live coverage map with parity probes |
| `GET /api/v1/coverage/status` | Map metadata |
| `GET /api/platform/connectors/coverage` | Platform alias |

### Display format

```
Binance: ✅ 245 pairs | Coinbase: ✅ 180 pairs | Bybit: ⚠️ 0 pairs (connectivity issue)
```

Live parity: HTTP probe per venue. If API down → ⚠️ immediately. No vanity "300+" claims.
