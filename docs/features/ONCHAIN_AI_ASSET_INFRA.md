# On-Chain, AI Content, Protocol, Portfolio & Asset Infrastructure — #510-#516

## #510 — Whale Flow Destination Tracker (🟡 Rename & Integrate)

| Rule | Implementation |
|------|----------------|
| Rename | → **Whale Flow Destination Tracker** (remove "AI Profiling") |
| Output | `Whale moved $X to [Exchange/Cold/DeFi] \| Confidence: heuristic-based` |
| Integration | On-Chain Intelligence Layer / Whale Intelligence Module |
| Method | Rule-based destination tagging |

API: `/api/platform/intelligence-ledger/onchain-layer/whale-flow-destination/*`

## #511 + #512 + #513 — AI Content Engine (🟢 Proceed as Layer)

Merged into single **AI Content Engine** (Sprint 2).

| Ticket | Sub-Module | Rename |
|--------|------------|--------|
| #511 | `market_evidence_feed` | AI Market Insights → **Market Evidence Feed** |
| #512 | `market_digest` | AI_Digest_Generator → **Market Digest Generator** |
| #513 | `multi_factor_opportunity_screener` | AI_Quant_Rating_Engine → **Multi-Factor Opportunity Screener** (🔴 restructured) |

### #513 Restructure (🔴 Block → Restructure)

| Blocked | Replacement |
|---------|-------------|
| "Rating Engine" | User-controlled screener |
| "0-100 investment score" | Factor Alignment Indicator |
| "Opportunity rank" | Sort by: [factor] — user sets weights |
| Learned scoring | Blocked until legal review + 6 months validation |

Pipeline: `rank(#513) → evidence(#511) → digest(#512)`

API: `/api/platform/intelligence-ledger/intelligence-layer/ai-content/*`

## #514 — Protocol Metrics Layer (🟢 Infrastructure — Sprint 0)

| Rule | Implementation |
|------|----------------|
| No standalone | Protocol Metrics Layer |
| Bot filtering | Documented heuristics mandatory |
| Output | DAU/MAU with filtered unique addresses |

API: `/api/platform/intelligence-ledger/data-layer/protocol-metrics/*`

## #515 — Portfolio Intelligence Layer (🟢 Sprint 1)

| Rule | Implementation |
|------|----------------|
| No standalone | Portfolio Layer / Historical Snapshot |
| Point-in-time | Reproducible snapshot hash |
| No leakage | Historical labels only |

API: `/api/platform/intelligence-ledger/portfolio-layer/snapshots/*`

## #516 — Asset Intelligence Profiles (🟢 Sprint 0 Foundation)

| Rule | Implementation |
|------|----------------|
| Priority | Highest — build before dependent features |
| Stable IDs | Immutable entity IDs |
| Duplicates | Resolved with merged aliases |
| Coverage | Research/intel/unlock/funding flags visible |

API: `/api/platform/intelligence-ledger/data-layer/asset-profiles/*`

## Layer Architecture

```
Data Layer (Sprint 0)
├── #514 Protocol Metrics Layer
└── #516 Asset Intelligence Profiles (foundation)

On-Chain Layer (Sprint 1)
└── #510 Whale Flow Destination Tracker

Portfolio Layer (Sprint 1)
└── #515 Portfolio Intelligence Layer

Intelligence Layer (Sprint 2)
└── #511+#512+#513 AI Content Engine
```
