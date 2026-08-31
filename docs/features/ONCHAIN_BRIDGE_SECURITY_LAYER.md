# On-Chain & Security Layer — #506 #507 #508

## #506 + #521 — Cross-Chain Bridge Flow Monitor

**Decision:** 🟡 Rename & Restructure — merge #521 into #506.

| Rule | Implementation |
|------|----------------|
| Rename | "Cross-Chain Bridge Volume Inflow" → **Cross-Chain Bridge Flow Monitor** |
| No AI | Removed "AI engine", "smart signals", ML, walk-forward testing |
| No performance claims | Sharpe ≥1.5, Win Rate ≥55%, Max Drawdown removed |
| Output = data | `Bridge X → Y: +$50M inflow \| Entity: Unknown/Tagged \| Confidence: data freshness` |
| Method | Rule-based indexing — count transactions + sum amounts |

API: `/api/platform/intelligence-ledger/onchain-layer/bridge-flow/*`

## #507 — Dusting Attack Detection Alert

**Decision:** 🟡 Rename & Proceed.

| Rule | Implementation |
|------|----------------|
| Rename | "Cross-Chain Wallet Dusting Attack Neutralizer" → **Dusting Attack Detection Alert** |
| Output = alert | "Potential dusting pattern detected on [address]" — NOT "blocked" |
| Disclaimer | "Detection based on heuristics \| False positives possible \| Not security guarantee" |
| Method | Rule-based heuristics — no AI required |

API: `/api/platform/intelligence-ledger/security-layer/dusting-detection/*`

## #508 — Exchange Flow Velocity Monitor

**Decision:** 🟡 Rename & Integrate — NOT standalone.

| Rule | Implementation |
|------|----------------|
| Rename | "Exchange Wallet Outflow Acceleration" → **Exchange Flow Velocity Monitor** |
| No prediction | Removed "Acceleration" (predictive connotation) |
| Output = data | `Outflow velocity: +200% vs 30-day average \| Entity: [Exchange]` |
| No portfolio language | Removed copy-paste portfolio management description |
| Integration | Feed within On-Chain Intelligence Layer |

API: `/api/platform/intelligence-ledger/onchain-layer/exchange-flow-velocity/*`

## Layer Architecture

```
On-Chain Layer (Sprint 1)
├── #506+#521 Cross-Chain Bridge Flow Monitor
└── #508 Exchange Flow Velocity Monitor (integrated feed)

Security Layer (Sprint 1)
└── #507 Dusting Attack Detection Alert
```
