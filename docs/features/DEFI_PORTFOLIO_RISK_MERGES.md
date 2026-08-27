# DeFi & Portfolio Risk Layer Merges — Features #482, #483, #484, #485, #488

## Summary

Five Sprint-2 features merged into existing layers — no standalone modules.

| Feature | Legal Name | Merged Into |
|---------|------------|-------------|
| #482 | Oracle Risk | #438 DeFi Opportunity Scanner (DeFi Risk Layer) |
| #483 | ROI & ATH Intelligence | #449 Portfolio Intelligence Engine (Portfolio AI) |
| #484 | Real-Time Risk Alerts | #410 Capital Protection Controls |
| #485 | Risk Analytics | #410 Capital Protection Controls |
| #488 | SOPR / Profitability Intelligence | #408 Smart Money Flow Tracker |

---

## #482 — Oracle Risk (→ #438 DeFi Layer)

Evaluates protocol dependency on price oracles. Source config + version documented per protocol.

### Indicators

1. Oracle count (single vs multi-source)
2. Heartbeat freshness
3. Deviation history
4. Dependency depth

### Integrations

| Integration | Behavior |
|-------------|----------|
| #410 Capital Protection | Alert if portfolio exposure in single-oracle protocol |
| #467 Stablecoin Health | Stablecoins with oracle risk flagged |

### Routes

```
GET /api/platform/intelligence-ledger/unified-arbitrage/defi/oracle-risk
GET /api/platform/intelligence-ledger/unified-arbitrage/defi/oracle-risk?protocol=aave
```

---

## #483 — ROI & ATH Intelligence (→ Portfolio AI)

Deterministic performance metrics with 7 mandatory ROI windows and ATH statistics.

### ROI Windows

`24h`, `7d`, `30d`, `90d`, `1Y`, `YTD`, `all_time`

### Outputs

| Output | Description |
|--------|-------------|
| ROI matrix | 7-window return from reference prices |
| ATH drawdown | Distance from all-time high |
| Recovery days | Days to recover from trough (when applicable) |
| Breakeven ROI | ROI from #404 Dynamic Cost Basis, not entry only |

Corporate/token events (splits, airdrops, burns) adjusted where relevant.

### Routes

```
GET /api/platform/intelligence-ledger/portfolio-ai/portfolio-intelligence/roi-ath
GET /api/platform/intelligence-ledger/portfolio-ai/portfolio-intelligence/roi-ath?asset=BTC
```

---

## #484 — Real-Time Risk Alerts (→ #410)

Backend-enforced threshold engine — alerts computed server-side, not client-side.

### Mandatory Thresholds

1. Drawdown %
2. Concentration %
3. Correlation spike
4. Exchange health drop

Push/email/SMS via existing notification infrastructure. Combined with #429 opportunity alerts.

### Routes

```
GET /api/platform/intelligence-ledger/portfolio-ai/capital-awareness/real-time-risk-alerts
GET /api/platform/intelligence-ledger/portfolio-ai/capital-awareness/opportunity-risk-combined
```

---

## #485 — Risk Analytics (→ #410)

VaR, liquidity risk, and stress analytics for Portfolio AI and Market Radar surfaces.

### Components

| Component | Requirement |
|-----------|-------------|
| VaR 95% / 99% | Parametric method with documented assumptions |
| Liquidity risk | Max exit size without >2% slippage |
| Stress analytics | 5 scenarios via #453 |
| Model validation | Assumptions documented in Terms of Service |

### Routes

```
GET /api/platform/intelligence-ledger/portfolio-ai/capital-awareness/risk-analytics
```

---

## #488 — SOPR / Profitability Intelligence (→ #408)

Spent Output Profit Ratio with transfer filtering and edge-case validation.

### Outputs

| Output | Description |
|--------|-------------|
| SOPR 7-day average | Filtered spent output ratio |
| Profit/loss regime | `profit_zone` vs `loss_zone` |
| Trend direction | `improving`, `declining`, `flat` |

### Edge Cases Tested

1. Exchange cold wallet movement
2. Staking deposit
3. Contract interaction

### Integrations

| Integration | Behavior |
|-------------|----------|
| Market Radar | SOPR in market health dashboard |
| #410 Capital Protection | Alert when SOPR < 1.0 + high portfolio exposure |

### Routes

```
GET /api/platform/intelligence-ledger/onchain-layer/smart-money-flow/sopr?asset=BTC
```

---

## Test Suite

```bash
.venv/bin/python -m pytest tests/test_defi_portfolio_risk_merges_batch.py -q
```
