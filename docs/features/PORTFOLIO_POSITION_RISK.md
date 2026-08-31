# Portfolio Position Risk — #366 #373 #377

## #366 Liquidation Risk — 🟡 Merge & Absorb

Cancelled as standalone ticket. Absorbed as **Position Stress Scenario** inside Portfolio AI.

| Rule | Implementation |
|------|----------------|
| Portfolio-level | Not Market Radar — user's own positions |
| No "Liquidation Risk" output | Renamed to Position Stress Scenario |
| Scenario assumptions lock | Scenario + assumptions + mathematical result shown |
| Educational not advice | "If price drops X%, your LTV becomes Y" |

API: `/api/platform/intelligence-ledger/portfolio-ai/position-stress-scenario`

## #373 Margin_Risk_Calculator — 🟠 Rename & Restrict (Wave 2)

Renamed to **Position Risk Context**.

| Rule | Implementation |
|------|----------------|
| No risk score | Component breakdown: margin utilization, liquidation distance, scenario losses |
| Venue rules versioned | Mandatory per venue |
| Stress tests mandatory | No liquidation distance without scenarios |
| No false precision | Ranges not exact numbers |
| Legal review | Mandatory before release |

API: `/api/platform/intelligence-ledger/portfolio-ai/position-risk-context`

## #377 Multi-Model Liquidation Comparison — 🟠 Hold & Block

Engineering blocked pending availability of multiple liquidation models (Model1/2/3).

| Rule | Implementation |
|------|----------------|
| Prerequisites | 0/3 models available — no engineering |
| No consensus heatmap | Consensus = interpretation — forbidden |
| Model disagreement | Required when eventually built |

Status API: `/api/platform/intelligence-ledger/portfolio-ai/multi-model-liquidation/status`
