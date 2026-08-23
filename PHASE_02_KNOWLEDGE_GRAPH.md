# PHASE 02 — Knowledge Graph

**Status:** ✅ Complete

## Deliverables
- `kg_nodes`, `kg_edges` tables
- Node types: Asset, Signal, Decision, Outcome, User
- Edge types: predicted, resulted_in, influenced_by
- APIs: `POST /api/kg/node`, `POST /api/kg/edge`, `GET /api/kg/query`
- Auto-ingest: `audit_registry.create_decision()` → `knowledge_graph.ingest_decision()`

## Verify
```bash
curl -sS "$BASE/api/compounding/_verify/phase/2"
curl -sS -X POST "$BASE/api/decisions" -H 'Content-Type: application/json' \
  -d '{"context":{"symbol":"BTC"},"prediction":{"action":"long"},"confidence":0.7}'
curl -sS "$BASE/api/kg/query?symbol=BTC&days=30"
```
