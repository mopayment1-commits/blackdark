# MCP Server for AI Agents — Feature #179

Read-only MCP wrapper around BLACKDARK API (#162). **No execution permissions.**

## Tools (5)

| Tool | Maps to |
|------|---------|
| `get_price` | `/api/v1/blackdark/price/{asset}` |
| `get_market_health` | `/api/v1/blackdark/market-health/{asset}` |
| `get_risk_score` | `/api/v1/blackdark/risk-score/{asset}` |
| `get_connector_registry` | Connector health registry |
| `get_daily_brief` | QuickTake published insights |

## Auth

- `BLACKDARK_MCP_API_KEY` or `X-API-Key` header required
- Every response includes `freshness` + `source_metadata`

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /mcp/status` | Server status |
| `GET /mcp/tools` | Tool schemas |
| `POST /mcp/tools/call` | Direct tool invocation |
| `POST /mcp/jsonrpc` | JSON-RPC 2.0 (MCP compatible) |

## Stdio mode

```bash
BLACKDARK_MCP_API_KEY=your-key python -m blackdark.mcp.server
```

## Acceptance

- Tool schemas tested
- Auth required
- Source/freshness metadata on all tool results
- Read-only — `execution_allowed: false`
