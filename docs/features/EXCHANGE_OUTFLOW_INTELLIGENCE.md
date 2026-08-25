# #242 Exchange Outflow Intelligence

**Sprint 2 — Intelligence | Integrated into Exchange Intelligence Hub (#734-736)**

## Overview

Measures on-chain asset outflows from labeled exchange clusters to external addresses. Integrated as the **outflow tab** inside the Exchange Intelligence Hub alongside inflow, netflow, exchange quality, and usage profile. **Not** a standalone dashboard.

Risk context only — answers "Is this exchange under pressure?" not "Should I sell?"

## Acceptance Criteria

| Criterion | Implementation |
|-----------|----------------|
| Closure with inflow/netflow | `Inflow - Outflow = Netflow` displayed on every outflow card |
| Reconciliation verified | Variance > 0.1% triggers internal alert |
| Cluster versioned | `Exchange Cluster v4.2` with per-exchange address counts |
| Anomaly detection | Spike vs 30D baseline — "Elevated Outflow Detected" |
| Exchange breakdown | Per-exchange amounts and percentages required |
| Address dedupe | Internal transfers excluded, unique address count |
| Chain validation | Per-chain asset amounts |
| Non-hideable disclaimer | `disclaimer_hideable: false` |
| Risk context only | No sell/withdraw language |
| Hub integration | Tab in Exchange Intelligence Hub #734-736 |

## API Endpoints

- `GET /api/platform/market-radar/exchange-hub/dashboard?asset=BTC` — full hub
- `GET /api/platform/market-radar/exchange-hub/outflow?asset=BTC` — outflow tab
- `GET /api/platform/market-radar/exchange-hub/inflow?asset=BTC` — inflow tab
- `GET /api/platform/market-radar/exchange-hub/netflow?asset=BTC` — netflow tab
- `GET /api/platform/market-radar/exchange-hub/status` — module status

## Files

- `bd_platform/exchange_outflow_intelligence.py` — #242 outflow module
- `bd_platform/exchange_inflow_intelligence.py` — inflow (closure pair)
- `bd_platform/exchange_netflow_intelligence.py` — netflow (reconciliation pair)
- `bd_platform/exchange_flow_common.py` — shared reconciliation logic
- `bd_platform/exchange_intelligence_hub.py` — hub #734-736
- `data/exchange_intelligence_hub_seed.json` — BTC, ETH, SOL seed data
- `tests/test_exchange_outflow_intelligence.py` — acceptance tests

## Disclaimer

> Exchange outflows represent on-chain movements from labeled exchange addresses to external addresses. Not all outflows indicate selling or distress. Internal wallet rebalancing may appear as outflow. Not investment advice.
