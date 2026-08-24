# Exchange Health Monitor — Feature #110

Withdrawal Status Alert system (renamed from "استغلال الفروق").

**Risk signal only** — NOT a guaranteed arbitrage strategy.

| Capability | Function | API |
|------------|----------|-----|
| Exchange health status | `exchange_health_status()` | `GET /api/platform/exchange-health/status` |
| Withdrawal alerts | `withdrawal_status_alerts()` | `GET /api/platform/exchange-health/alerts` |

## Integrations

- **#134** — `platform_status_134` from `platform_universe`
- **#109** — `feeds_portfolio_risk_109` when red flags detected
- Data: `data/exchange_health_snapshots.jsonl`

## Legal disclaimer

All responses include `legal_disclaimer`. No profit promises — withdrawal restrictions
are surfaced as operational / insolvency risk signals.

## Acceptance criteria

| Criterion | Target |
|-----------|--------|
| API latency | ≤2s (`sla_met`) |
| Mode | `risk_signal_only` |
| Updates | Real-time from health snapshot feed |
