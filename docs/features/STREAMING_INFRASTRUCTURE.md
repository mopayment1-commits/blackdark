# Streaming Infrastructure — #218 + #222 (Sprint 0)

Real-Time Feed + WebSocket streaming merged. **#222 closed** — WebSocket is transport within Freshness Assurance (#219).

## Institutional Rules

| Rule | Implementation |
|------|----------------|
| Latency SLO | `Latency: < 500ms` |
| Gap handling | `Gap: auto-backfill` |
| Reconnect SLO | `Reconnect: < 3s` |
| Stream multiplexing | Single WS connection for multiple assets |
| Backfill on reconnect | No data loss on disconnect |
| Health monitoring | Admin dashboard at `/streaming/health` |
| Rate limiting | Per-client message rate cap |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/streaming/status` | Module status |
| `GET /api/platform/streaming/slos` | Latency/gap/reconnect SLOs |
| `GET /api/platform/streaming/multiplex` | Multiplexed feed config |
| `GET /api/platform/streaming/health` | Connection health (admin) |
| `POST /api/platform/streaming/backfill` | Trigger backfill |
| `WS /ws/platform/stream` | Multiplexed WebSocket feed |

## Related

- `bd_platform/freshness_assurance.py` — #219 Freshness Assurance Layer
- `bd_platform/platform_streaming_hub.py` — WebSocket hub
