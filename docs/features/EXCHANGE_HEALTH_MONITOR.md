# Exchange Health Monitor — Feature #456

Sprint-2 Risk Layer (renamed from Exchange Insolvency Risk Scraper). Transparent exchange health grading — not a solvency determination.

## Endpoints

| Route | Description |
|-------|-------------|
| `GET /api/platform/intelligence-ledger/portfolio-ai/exchange-health/status` | Feature status |
| `GET /api/platform/intelligence-ledger/portfolio-ai/exchange-health` | Full health panel + grades |
| `GET /api/platform/intelligence-ledger/portfolio-ai/exchange-health/grades` | Exchange Grade (A+ to F) list |
| `GET /api/platform/intelligence-ledger/portfolio-ai/exchange-health/exposure-alerts` | #410 exposure alerts |
| `GET /api/platform/intelligence-ledger/portfolio-ai/exchange-health/arbitrage-filter` | Arbitrage health filter |

## Indicators (weighted)

1. Proof-of-reserves ratio (liabilities/assets) — 30%
2. Hot wallet flow anomaly — 20%
3. Withdrawal suspension history — 20%
4. Regulatory actions — 15%
5. Social panic signals — 15%

## Integrations

- **#410 Capital Protection:** Alert when portfolio exposure > 20% on low-health exchange (Grade F, D-, D, D+)
- **Arbitrage (#403/#429):** Auto-suppress opportunities involving low-health venues

## Cancelled acceptance criteria

Infrastructure SLAs (≤2s response, ≥95% accuracy, 99% uptime) are not product acceptance criteria for this feature.
