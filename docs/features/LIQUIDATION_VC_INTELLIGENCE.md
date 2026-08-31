# Liquidation & Private Market Intelligence — #307 #311 #314

## #307 Liquidation Cluster Analytics — 🟡 Wave 2

Renamed from **Imminent Liquidation Cluster Scanning**.

| Rule | Implementation |
|------|----------------|
| No "imminent" / "scanning" | Data display only |
| No prediction | Clusters = historical + current OI |
| Estimated levels | Probability only — not certainty |
| Sources | Exchange APIs + on-chain perp \| confidence per venue |

API: `/api/platform/intelligence-ledger/liquidation-clusters/*`

## #311 Basis Intelligence — 🔴 Rejected standalone

Merged as **sub-metric view** in Derivatives Market State Module (#327).

- Annualized basis with expiry/time alignment
- "Basis chart" = line on chart — not a separate module

## #314 Private Market & VC Flow Intelligence — 🟢 Wave 2

| Rule | Implementation |
|------|----------------|
| Data sources | Crunchbase + Messari Pro + TheBlock + manual \| PitchBook = Phase 2 |
| Currency | USD at announcement date \| FX documented |
| Outliers | Mega-rounds >$500M flagged + context |
| Revisions | Versioned \| previous values archived |
| Scope | Crypto-native only \| Grants excluded |

API: `/api/platform/intelligence-ledger/private-market-vc/*`
