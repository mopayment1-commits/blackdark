# Portfolio VaR Metric (Sprint 2)

**Merged into Portfolio AI Risk Tab · Insight-only · No Protection**

Historical percentile VaR — risk measurement, NOT a loss guarantee.

## Methodology

Rule-based historical simulation:
- Percentile of daily returns over 90-day lookback
- Configurable confidence (90% / 95% / 99%) and horizon (1d / 7d / 30d)
- Decimal precision via #1031 Financial Precision Policy
- No Monte Carlo / ML in Sprint 2

## Output example

> Historical VaR (95%): on 95% of historical days, portfolio daily loss did not exceed $X.

## Hit rate

Published to Accuracy Ledger (#987) — breach days visible, no hiding.

## API

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/portfolio-var/status` | Methodology status |
| `GET /api/platform/portfolio-var/e2e` | E2E self-test |
| `POST /portfolio/analyze` | Includes `var_metric` block |

## Integrations

- #907 Multi-Account Sync — positions input
- #959 Reference Pricing — price input
- #967 Historical Data — returns series
- #945 Provenance — dataset version metadata
- #987 Accuracy Ledger — hit rate publication

## Disclaimer

Low VaR ≠ safe portfolio. Risk Tab warns — does not protect.
