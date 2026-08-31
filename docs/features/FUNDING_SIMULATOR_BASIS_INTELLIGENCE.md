# Funding Simulator & Basis Intelligence — #338 #341 #343

## #338 Funding Arbitrage Simulator — 🟠 Rename & Restrict (Wave 3)

Renamed from **Funding_Arbitrage_Engine**.

| Rule | Implementation |
|------|----------------|
| No "Engine" in name | Renamed to Funding Arbitrage Simulator |
| Paper/simulation ONLY | No live execution, no exchange API integration |
| Legal review mandatory | Release blocked until compliance gate passes |
| No opportunity language | "Ranked by hypothetical net spread" not "Best opportunity" |
| All costs mandatory | Fees, borrow, slippage, basis risk, liquidity penalties |
| No guaranteed profit | Hypothetical analysis disclaimer on every output |

API: `/api/platform/intelligence-ledger/funding-arbitrage-simulator/*`
Tier: Pro/Institution only (Wave 3)

## #341 Fundraising Velocity Indicator — 🟠 Rename & Restructure (Wave 2)

Renamed from **Fundraising Momentum Score**.

| Rule | Implementation |
|------|----------------|
| No "Score" in name/output | Component breakdown: velocity, breadth, stage |
| Formula lock | Documented + versioned + backtested |
| No undisclosed valuation | Undisclosed = excluded, no estimation |
| No ranking by score | Activity breakdown only |
| Merged into | Market Radar / Project Intelligence |

API: `/api/platform/intelligence-ledger/market-radar/fundraising-velocity`

## #343 Futures Basis & Term Structure — 🟡 Merge & Absorb

Cancelled as standalone ticket. Absorbed as **Basis Curve** in Market Radar / Derivatives Panel.

| Rule | Implementation |
|------|----------------|
| No basis trading signals | Backwardation/contango = mathematical labels only |
| Expiry math verified | Annualization + days-to-expiry with UTC sync |
| Venue normalization | Mandatory per contract |
| No implied carry claims | No forward-looking performance claims |

API: `/api/platform/intelligence-ledger/market-radar/basis-curve`
