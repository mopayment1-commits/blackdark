# #239 Digital Asset Treasury Company Intelligence

**Sprint 2 — Intelligence | Integrated into Macro Hub #263**

## Overview

Tracks public companies with digital asset treasuries (DAT companies). Provides filing-sourced holdings data, normalized treasury exposure, and stock-crypto linkage metrics. Integrated as a card inside the Macro Intelligence Hub — **not** a standalone product.

## Acceptance Criteria

| Criterion | Implementation |
|-----------|----------------|
| Filing/source timestamps | Every holding includes SEC/SEDAR+ source, form, filed date, reporting period |
| No stale as live | Holdings > 45 days old marked `Stale`; estimates shown separately with low confidence |
| Treasury exposure normalized | BTC per share, % market cap, cost basis, unrealized P&L |
| Crypto linkage visible | 90D stock-BTC correlation, beta, exposure level |
| Dashboard structure | Company, treasury value, cost basis, correlation, filing dates |
| No buy language | Context: "BTC proxy" — never "Buy MSTR" |
| Non-hideable disclaimer | `disclaimer_hideable: false` |
| Macro context only | No yield/arbitrage — analysis only |
| Coverage minimum | Top 20 public DAT companies tracked |
| Macro Hub integration | Card in #263 dashboard via `treasury_companies` module |

## Staleness Policy

- **Live**: reporting period end ≤ 45 days ago
- **Stale**: > 45 days — shown as "Last Disclosed" with age, never "Live Treasury"
- Stale holdings may include heuristic estimates with `Confidence: Low`

## API Endpoints

- `GET /api/platform/market-radar/macro-hub/treasury-companies?asset=BTC`
- `GET /api/platform/market-radar/macro-hub/treasury-companies/{ticker}`
- `GET /api/platform/market-radar/treasury-intelligence/status`

## Integration (#263)

`macro_intelligence_hub._aggregate_modules()` includes `treasury_companies` card with live status.

## Files

- `bd_platform/treasury_intelligence.py` — core module
- `data/treasury_intelligence_seed.json` — 20 DAT companies
- `bd_platform/macro_intelligence_hub.py` — hub integration
- `tests/test_treasury_intelligence.py` — acceptance tests

## Disclaimer

> Treasury data based on public company filings. Holdings may have changed since last disclosure. Unrealized P&L is an estimate. Not investment advice.
