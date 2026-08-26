# Reference Data & Volatility Infrastructure — #394 #395 #501

## #394 Reference Data Registry — 🟢 Build (Internal, Wave 0)

Renamed from standalone "Reference Data API" ticket.

| Rule | Implementation |
|------|----------------|
| No API as product | Internal tool only — no external API product |
| Stable IDs | Mandatory — immutable canonical IDs |
| Versioned mappings | Mandatory — no breaking changes |
| Lifecycle handling | Corporate/token lifecycle tracked (delist, rebrand, merge) |
| Priority | Wave 0 — highest priority infrastructure |

API (internal): `/api/platform/internal/reference-data-registry/*`

## #395 Spot & Derivatives Coverage — 🟡 Merge & Absorb

Cancelled as standalone ticket. Absorbed as **Market Data Normalization Layer** in Market Data Engine (#274).

| Rule | Implementation |
|------|----------------|
| No coverage as product | Infrastructure layer only |
| Contract specs validated | Mandatory per derivative |
| No asset mismatch | Mismatched contracts excluded |
| Cross-venue normalization | Spot + perp + futures + options unified |

API: `/api/platform/intelligence-ledger/market-radar/market-data-normalization`

## #501 Volatility Scoring System — 🟡 Rename & Restructure (Sprint 1)

Renamed to **Cross-Asset Volatility Regime Analyzer**.

| Rule | Implementation |
|------|----------------|
| No scoring terminology | No "risk score" in name/output |
| Historical percentile | Historical Volatility Percentile (0–100) |
| Regime classification | Historical context only — relative to asset distribution |
| No advisory language | No buy/sell implication |
| Legal review | Mandatory; 3-month rule-based baseline |
| ML deferred | Until compliance framework complete |

API: `/api/platform/intelligence-ledger/data-layer/volatility-regime/*`
