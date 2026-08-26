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

## Regime Classification (#328)

Rule-based thresholds — **Regime Classification Sub-component** (standalone rejected):
- **Crowded** — elevated funding + OI
- **Flush** — liquidation spike
- **Normal** — default state
- Formula versioned; backtest gate required

## Estimated Leverage Ratio (#329)

`ELR = OI / Exchange Reserve | Formula versioned | Variants documented`

- Reserve = 0 or missing → ELR = N/A
- Historical percentile: 90-day rolling window
- Denominator QA: verified on-chain or exchange attestation

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
