# Economic Calendar — #211

Sprint 1 — TradingView Economic Calendar widget import + asset relevance layer.

**NOT built from scratch.** Distinct from #140 Macro Events Calendar (RSS news + impact headlines).

## Institutional Rules

| Rule | Implementation |
|------|----------------|
| Import, don't build | TradingView Economic Calendar widget config |
| Source tracked | `Event: CPI \| Source: BLS \| Timezone: EST \| Revision: v1 (preliminary)` |
| Factual display | `Forecast: X% \| Previous: Y% \| Actual: Z%` |
| Not trade advice | No "Buy BTC before FOMC" — historical volatility context only |
| Asset relevance | `FOMC Decision → BTC volatility historically +5.2% in 24h` |
| Disclaimer | Non-hideable: "Economic data is factual reporting, not investment advice." |

## Sprint 2 Deferred

- ForexFactory API supplemental import
- Live revision updates when actuals are released

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/economic-calendar` | List events (filter by asset/country/category/impact) |
| `GET /api/platform/economic-calendar/{id}` | Event detail with source/timezone/revision |
| `GET /api/platform/economic-calendar/relevance/{asset}` | Asset relevance summary |
| `GET /api/platform/economic-calendar/widget` | TradingView widget embed config |
| `GET /api/platform/economic-calendar/status` | Module status |

## Related

- **#140** Macro Events Calendar — RSS news stream with impact forecasting (`/market-radar/macro-events`)
- **#18** Crowdsourced Event Calendar — CoinMarketCal (`/events/calendar`)
