# Intelligence & Risk Layer Merges — Features #467, #472, #474

## Summary

Three high-priority features merged into existing layers — no standalone modules.

| Feature | Legal Name | Merged Into |
|---------|------------|-------------|
| #467 | Stablecoin Health Monitor | #410 Capital Protection Controls (Risk Layer) |
| #472 | Investment Thesis Scoring | Intelligence Ledger |
| #474 | Daily Market Brief | Intelligence Ledger / Market Radar |

---

## #467 — Stablecoin Health Monitor (→ #410 Risk Layer)

Renamed from "De-Pegging Probability Index" — no "De-Pegging" in legal name.

### Indicators

1. Price deviation from $1
2. Redemption pressure (exchange outflow)
3. Collateral ratio (backed stablecoins)
4. Funding rate anomaly
5. Social panic signals

### Outputs

| Output | Description |
|--------|-------------|
| `stablecoin_grade` | AAA through D competitive grade |
| `depeg_probability` | Monitoring index (not guarantee) |
| Portfolio alerts | Exposure > 30% in threatened asset (#410) |
| Arb cancellation | Stablecoin arb cancelled if depeg prob > threshold (#429) |

Cancelled SLA: response ≤2s, accuracy ≥95%, uptime 99%, real-time update.

### Routes

```
GET /api/platform/intelligence-ledger/portfolio-ai/capital-awareness/stablecoin-health/status
GET /api/platform/intelligence-ledger/portfolio-ai/capital-awareness/stablecoin-health
GET /api/platform/intelligence-ledger/portfolio-ai/capital-awareness/stablecoin-health/alerts
GET /api/platform/intelligence-ledger/portfolio-ai/capital-awareness/stablecoin-health/reconciliation-tests
```

---

## #472 — Investment Thesis Scoring (→ Intelligence Ledger)

Evidence-weighted rubric — **not price probability** (documented in UI and Terms).

### 6 Mandatory Dimensions

1. Team quality
2. Tokenomics
3. Revenue model
4. Competitive moat
5. Regulatory risk (inverted)
6. On-chain growth

### Integrations

| Integration | Behavior |
|-------------|----------|
| #417 Net-Edge Score | Thesis score adjusts signal confidence |
| Market Radar | Asset card shows thesis grade (A–F) |

### Routes

```
GET /api/platform/intelligence-ledger/investment-thesis/status
GET /api/platform/intelligence-ledger/investment-thesis
GET /api/platform/intelligence-ledger/investment-thesis/market-radar-card?asset=BTC
GET /api/platform/intelligence-ledger/investment-thesis/reconciliation-tests
```

---

## #474 — Daily Market Brief (→ Intelligence Ledger / Market Radar)

Renamed from "Market Regime Written Read". Template-based generation from actual contributors — no generic AI prose in v1.

### Output Structure (3 sections only)

1. **What Changed** — regime shifts + top contributor deltas
2. **Why** — lens directions + supporting metrics
3. **Risks** — volatility, upcoming events (#443)

Every sentence backed by evidence link. Contributors must match calculations (backtest validated).

### Integrations

| Integration | Behavior |
|-------------|----------|
| Market Radar | Daily Brief appears first on dashboard |
| #443 Event Monitor | Events included in narrative risks section |

### Routes

```
GET /api/platform/intelligence-ledger/daily-market-brief/status
GET /api/platform/intelligence-ledger/daily-market-brief
GET /api/platform/intelligence-ledger/daily-market-brief/market-radar
GET /api/platform/intelligence-ledger/daily-market-brief/reconciliation-tests
```

Market Radar unified feed also exposes `daily_brief_474` and `thesis_cards_472`:

```
GET /api/platform/intelligence-ledger/unified-arbitrage/market-radar
```
