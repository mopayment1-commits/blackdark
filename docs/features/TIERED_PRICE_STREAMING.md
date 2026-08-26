# Tiered Price Streaming — #128 (Enterprise Sub-Second Only)

## Institutional Decision

**🟡 Enterprise Tier Only — NOT built for everyone.**

Sub-second price updates are resource-intensive. Dedicated infrastructure is reserved for paying enterprise/institution clients.

| Tier | Refresh SLA | Mode |
|------|-------------|------|
| Free | 1–5 seconds | REST poll (no sub-second resources) |
| Pro+ | 500ms | Shared WebSocket |
| Institution | 50–100ms | Dedicated WebSocket |
| Enterprise | 50–100ms | Dedicated WebSocket |

Extends **#283 Price Feed Layer** — not standalone.

## Acceptance Criteria

| Criterion | Implementation |
|-----------|----------------|
| Enterprise sub-second only | Backend blocks free tier sub-second requests |
| Free tier 1–5s | REST poll, `sub_second_allowed: false` |
| Pro tier 500ms | Shared WebSocket |
| Institution/Enterprise 50–100ms | Dedicated WebSocket |
| Response ≤2s | Enforced in metrics |
| Accuracy ≥95% | Per-tier accuracy tracking |
| Uptime 99% | Per-tier uptime tracking |
| Backend enforcement | `enforce_tier_access()` blocks unauthorized tiers |

## API

```
GET /api/platform/price-feed/tiered-streaming/status
GET /api/platform/price-feed/tiered-streaming?tier=enterprise&asset=BTC
GET /api/platform/price-feed/tiered-streaming/sla-tests
```

Free tier requesting sub-second (`requested_interval_ms < 1000`) returns **403**.

## Resource Rationale

Sub-second streaming on free tier costs more than it returns. Free users get 1–5s REST poll which is sufficient for retail analysis. Enterprise clients paying for dedicated infrastructure get 50–100ms dedicated WebSocket feeds.
