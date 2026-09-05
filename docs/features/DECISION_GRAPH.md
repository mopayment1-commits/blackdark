# Feature #47 — Decision Graph (Causal, Interactive)

AI-generated causal graph explaining **why** markets moved — not a static flowchart.

## Requirements met

| Requirement | Implementation |
|-------------|----------------|
| Interactive | Nodes are clickable; `GET .../decision/graph/node?node_id=` expands upstream/downstream |
| AI-generated | Built live from `decision_engine_inputs` + oracle labels |
| Causal | Edges: `because`, `then`, `influenced`, `triggered`, `resulted_in` |
| Real data | Macro (#104), on-chain flows, order flow, news, CVD |

## Example narrative

> Bitcoin down 3% while DXY up 0.5% → Large ETH inflow to exchange → AI decision context: elevated risk

## APIs

| Endpoint | Purpose |
|----------|---------|
| `GET /api/platform/decision/graph?asset=BTC` | Full causal graph |
| `GET /api/platform/decision/graph/node?node_id=` | Interactive node expansion |
| `GET /api/public/decision-graph` | Public honesty surface (delegates to causal builder) |

## SLA

Target ≤2 seconds (`sla_met` in response).

## Disclaimer

Educational transparency — not financial advice.
