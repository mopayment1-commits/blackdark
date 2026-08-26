# Historical Vault & Market Intelligence — #738 #739 #740 #741 #742 #743 #744

## #738 Historical Data Vault — 🟢 Sprint 0 (Infrastructure)

- **Checksums:** SHA-256 mandatory on every file/dataset version
- **Storage:** Append-only versioned — no overwrite
- **Reproducibility:** Pinned query manifests return identical checksums across runs
- **Granularity tiers:** Free = daily | Pro = hourly | Enterprise = tick-level
- **Delivery:** API + file download paths
- **Retention:** Tick: 1 year | Hourly: 5 years | Daily: forever

API: `/api/v1/data/historical-vault/*`

## #739 Index Data — Sprint 2 (Market Data API)

- **NOT standalone** — merged into Market Data API
- Uses CoinGecko / CCData — no proprietary index engine
- Methodology documented: "Rebalanced monthly | Market-cap weighted | Top 100"
- Version visible: "Index v2.1 | Last Rebalance: YYYY-MM-DD"

API: `/api/platform/intelligence-ledger/market-data/indices/*`

## #740 M&A Intelligence Module — 🟢 Sprint 2

- Deal status/source visible: "Status: Rumored/Confirmed/Closed | Source: CoinDesk/SEC Filing"
- Undisclosed value remains unknown — no fabricated valuation
- Comparable deals normalized by sector + date range + deal type
- Trends dashboard: volume by quarter, sector heatmap, top acquirers
- Disclaimer non-hideable

API: `/api/platform/intelligence-ledger/ma-intelligence/*`

## #741 MVRV Z-Score Dynamic Realignment — Sprint 2 (On-Chain Metrics Suite)

- Absorbed into On-Chain Metrics Suite (#737) — NOT standalone
- Independent calculation with dynamic realignment window
- Target: ≤2s latency, 95% accuracy, 99% uptime

API: `/api/platform/intelligence-ledger/onchain-metrics?asset=BTC`

## #742 Smart Screener — 🟢 Sprint 1 (Market Radar)

- Deterministic — same filters = same results
- Missing data explicit: "N/A"
- Saved filters — user can save and share
- Unique filters: Bot Activity (#721), Exchange Quality (#132), On-Chain Signal
- Language: "Assets matching your criteria: X" — not "opportunities"
- Fee DB (#130) required for yield/profit filters
- Free tier ≤3s | Pro tier sub-second

API: `/api/platform/intelligence-ledger/market-radar/screener/*`

## #743 Surveillance Engine — 🟢 Sprint 2 (Enterprise tier)

- Absorbs #721 Bot Activity as sub-module
- Rule-based pattern detection first (wash trading, spoofing)
- False-positive review pipeline — manual review before public alert
- Evidence retention: 90 days minimum
- Anonymized entities: "Exchange X" / "Asset Y"
- Enterprise tier: full alerts | Free tier: summary stats only

API: `/api/platform/intelligence-ledger/surveillance/*`

## #744 Options Context Module — 🟢 Sprint 2 (BTC/ETH)

- Max Pain / Gamma context — NOT a signal or prediction
- No causal guarantee disclaimer non-hideable
- Formula/version explicit: "Deribit OI | Methodology v1.1"
- Limitations visible: BTC/ETH only, excludes CME, daily update
- Data quality score: High/Medium/Low

API: `/api/platform/intelligence-ledger/options-context/*`
