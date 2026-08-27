# Sharpe, DeFi Contract Risk & Strategy Vetting — Features #490, #491, #492

## Summary

Three Sprint-2 features merged into existing layers — no standalone modules.

| Feature | Legal Name | Merged Into |
|---------|------------|-------------|
| #490 | Sharpe Ratio Intelligence | #449 Portfolio Intelligence Engine |
| #491 | Smart Contract and Protocol Risk | #438 DeFi Opportunity Scanner |
| #492 | Strategy Vetting Algorithm | Intelligence Ledger (Strategy Quality Gate) |

---

## #490 — Sharpe Ratio Intelligence (→ Portfolio AI)

Risk-adjusted return analytics with explicit risk-free policy and no cross-window comparison.

### Rolling Windows

`30d`, `90d`, `1y` — each window is self-contained (no comparing 30d Sharpe to 1y Sharpe).

### Risk-Free Policy

- Version documented (`1.0`)
- Source: 3-month T-bill proxy (fallback zero if unavailable)
- Rate explicit in every window output

### Outputs

| Output | Description |
|--------|-------------|
| `sharpe_ratio` | Annualized Sharpe per window |
| `percentile_vs_sector` | Competitive percentile vs sector average |
| `trend` | improving / declining / flat |
| `explanation` | Plain-language risk-adjusted return explanation |

### Integration

- **#474 Daily Market Brief**: Sharpe 90d trend appears in `what_changed` narrative

### Routes

```
GET /api/platform/intelligence-ledger/portfolio-ai/portfolio-intelligence/sharpe
```

---

## #491 — Smart Contract and Protocol Risk (→ #438 DeFi Layer)

Protocol-level contract risk using external data sources (DeFiLlama, Immunefi) — no internal scanner v1.

### 5 Mandatory Indicators

1. Contract verified (Etherscan)
2. Audit history (CertiK, OpenZeppelin, etc.)
3. Bug bounty active
4. Admin keys renounced
5. Upgradeability model

Cancelled SLA: response ≤2s, accuracy ≥95%, uptime 99%, real-time update.

### Integration

- **#460 Diligence Risk**: protocol risk adjusts opportunity score in DeFi scanner feed

### Routes

```
GET /api/platform/intelligence-ledger/unified-arbitrage/defi/smart-contract-risk
GET /api/platform/intelligence-ledger/unified-arbitrage/defi/smart-contract-risk?protocol=aave
```

---

## #492 — Strategy Vetting Algorithm (→ Intelligence Ledger)

Strategy Quality Gate — multi-factor vetting before display or paper-trading reliance.

### 6 Mandatory Factors

1. Backtest length
2. Out-of-sample period
3. Max drawdown
4. Turnover
5. Sharpe stability
6. Regime coverage

### Penalties & Gates

| Rule | Behavior |
|------|----------|
| Guaranteed-return claims | Auto-reject (grade F, ineligible) |
| Small sample | < 100 trades → ineligible |
| Overfit | Live Sharpe << backtest → score penalty |
| Display threshold | Grade ≥ B required for user display |

Thresholds versioned — each release documents `thresholds_version`.

### Integrations

| Integration | Behavior |
|-------------|----------|
| #429 Unified Arbitrage | Only grade ≥ B strategies shown; ineligible linked opps suppressed |
| #421 Strategy Simulator | Paper portfolio uses approved strategies only |

### Routes

```
GET /api/platform/intelligence-ledger/strategy-vetting/status
GET /api/platform/intelligence-ledger/strategy-vetting
GET /api/platform/intelligence-ledger/strategy-vetting/{strategy_id}
GET /api/platform/intelligence-ledger/strategy-vetting/reconciliation-tests
```

---

## Test Suite

```bash
.venv/bin/python -m pytest tests/test_sharpe_defi_strategy_merges_batch.py -q
```
