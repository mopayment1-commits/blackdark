# Feature #57 — Flash-Crash Protection Engine

AI circuit breaker for flash crashes, pumps, and cross-exchange anomalies.

## Circuit Breaker Levels

| Level | Trigger | Action |
|-------|---------|--------|
| Green | Normal | Full signals |
| Yellow | >2% in 60s | Delay signals 30s |
| Orange | >3% in 60s | Pause new signals |
| Red | >5% in 60s | Safe mode — all signals halted |

## Event Types

- `flash_crash` — halt buy signals
- `flash_pump` — halt sell signals
- `exchange_specific_crash` — divergence >1.5% between venues
- `liquidation_cascade` — extreme velocity

## APIs

| Endpoint | Purpose |
|----------|---------|
| `GET /api/platform/flash-crash/evaluate?asset=BTC` | Full evaluation + classification |
| `GET /api/platform/flash-crash/status` | Dashboard circuit breaker bar |

## Decision Engine integration (#48)

Sends `pause` / `delay` / `resume` via `flash_crash_protection` input.
Increases `risk_score_delta` when signals paused.

## Related features

- #48 Decision Engine — receives pause/resume
- #85 Order Flow — aggressive selling early warning
- #54 Exchange Netflow — whale outflow spike signal
