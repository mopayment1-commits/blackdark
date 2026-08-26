# Derivatives Market State Module — #327 (Sprint 2 Intelligence Ledger)

Renamed from **Derivatives Market Sentiment Composite** → **Derivatives Market State Module**.

The derivatives product — absorbs **#328** (regime) + **#329** (leverage ratio).

## Mandatory rules

| Rule | Implementation |
|------|----------------|
| **No opaque score** | Weighted sum — formula public + versioned |
| **Weights** | Funding 25%, OI 25%, Leverage 20%, Liquidations 15%, Price 15% |
| **Contributor evidence** | Every score = breakdown by component with value + contribution % + trend |
| **Backtest gate** | Regime labels backtested; FP rate < 30% |
| **Scope** | Perpetuals only; futures expiry = Phase 2; options = Phase 3 |

## Regime detection (#328)

Rule-based thresholds:
- **Crowded** — elevated funding + OI
- **Flush** — liquidation spike
- **Normal** — default state

## Leverage ratio (#329)

`Long/Short Ratio = OI_long / OI_short | Source: Binance API | Confidence: High`

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/intelligence-ledger/derivatives-market-state/status` | Module status |
| `GET /api/platform/intelligence-ledger/derivatives-market-state` | Market state panel |

## Acceptance criteria

- No opaque score ✅
- Formula/version + contributor evidence ✅
- Backtest documented ✅
- Perpetuals scope lock ✅
