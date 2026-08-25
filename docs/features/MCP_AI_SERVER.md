# MCP for AI — #262 (Sprint 2, AI Infrastructure)

MCP Server exposing canonical market data to AI agents with tool traceability and Verifiable AI grounding (#230).

## Institutional Rules

| Rule | Implementation |
|------|----------------|
| Tool traceability | `agent_id, tool_called, parameters, timestamp, response_hash` — 90-day retention |
| No model-only facts | Every response via #230 grounding with `evidence[]` |
| Schema documented | Machine-readable `inputSchema` / `outputSchema` / `examples` per tool |
| Rate limiting | Free 50/day \| Pro 5K/day \| Enterprise unlimited + priority |
| Authentication | `X-API-Key` + `X-Agent-Fingerprint` — no anonymous access |
| Disclaimer mandatory | `Data provided by BLACKDARK MCP Server \| Timestamp: ... \| Not investment advice.` |
| Fail-closed | `Data unavailable` error — no null or guess |
| #230 integration | Same grounding layer as users and internal AI |
| Versioning | MCP Server v1.0 \| Compatible: MCP spec 2025-03 |

## Tools

| Tool | Description |
|------|-------------|
| `blackdark_get_price` | Canonical spot price with evidence |
| `blackdark_get_onchain_metric` | MVRV, SOPR, NVT via Oracle path |
| `blackdark_get_exchange_quality` | Exchange connectivity + quality score |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/mcp/status` | Server status + acceptance criteria |
| `GET /api/platform/mcp/tools/schema` | Machine-readable tool schemas |
| `POST /api/platform/mcp/tools/call` | Execute tool (auth headers required) |
| `GET /api/platform/mcp/trace` | Tool call trace log |

### Authentication Headers

```
X-API-Key: <api_key>
X-Agent-Fingerprint: <agent_fingerprint>
```

## Response Contract

```json
{
  "ok": true,
  "asset": "BTC",
  "price_usd": 98500.0,
  "evidence": [{
    "fact": "BTC price $98500.0",
    "source_api": "Unified API price",
    "timestamp": "2026-08-25T13:20:00Z",
    "freshness_ms": 80,
    "confidence": "verified"
  }],
  "disclaimer": "Data provided by BLACKDARK MCP Server | Timestamp: ... | Not investment advice.",
  "disclaimer_hideable": false,
  "mcp": {
    "feature_id": 262,
    "server_version": "1.0",
    "mcp_spec": "2025-03",
    "grounding_layer": "#230",
    "trace_recorded": true
  }
}
```

## Related

- `bd_platform/verifiable_ai_engine.py` — #230 Grounding Layer
- `bd_platform/unified_api_platform.py` — #162 Oracle API parity
- `bd_platform/connector_coverage_map.py` — Exchange quality probes
