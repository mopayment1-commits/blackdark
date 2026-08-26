# Market Radar Funding Data — #331 #333 (absorbed into #274)

## #331 Funding / OI / Liquidation Metrics — 🟡 Merge & Absorb

Cancelled as standalone ticket. Absorbed as **Derivatives Venue Feed** inside **Market Data Engine (#274)**.

| Rule | Implementation |
|------|----------------|
| No standalone naming | Merged into Market Data Engine — no product page |
| No trading signal mask | Raw display: "Funding Rate = 0.01%" only |
| Provider semantics | Unified schema per venue; freshness SLA; fallback source |
| Surface | `market_data_display` — NOT Intelligence |
| No dashboard | Feeds engine; APIs counted as COGS |

API: `/api/platform/intelligence-ledger/market-radar/derivatives-venue-feed/*`

## #333 Funding Rate Intelligence — 🟡 Merge & Absorb

Cancelled as standalone ticket. Renamed to **Funding Rate Context Panel** inside Market Radar.

| Rule | Implementation |
|------|----------------|
| No "Intelligence" in name | Renamed to Funding Rate Context Panel |
| No trading signal mask | Weighted funding rate display only — no squeeze/opportunity language |
| Weighting documented | Formula, outlier threshold (z>3), settlement sync logic |
| No dashboard | Feeds engine; no separate sprint |

API: `/api/platform/intelligence-ledger/market-radar/funding-rate-context/*`

## Legal guardrails

- No "Funding Rate Divergence Signal" or "Liquidation Predictor" before 6-month rule-based baseline + legal review
- Gap between "data exists" and "data means buy" = legal liability boundary
- All output under Market Data Display, not Intelligence
