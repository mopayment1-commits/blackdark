# Oracle VWAP / Fair Value Index — Feature #413

Oracle API enhancement (merged with #409). Volume-weighted fair value across 10–15 major liquidity venues — not a standalone Rate API.

## Endpoints

| Route | Description |
|-------|-------------|
| `GET /api/oracle/fair-value-index/{symbol}` | Fair Value Index with constituent/source metadata |
| `GET /api/oracle/vwap/status` | Feature status |
| `GET /api/platform/intelligence-ledger/oracle-vwap/*` | Intelligence Ledger integrations |

## Integrations

- **Arbitrage Scanner (#403):** VWAP benchmark instead of best bid/ask
- **Market Radar:** Per-venue deviation % from fair value
- **Live Breakeven (#404):** VWAP reference price for breakeven calculations

## Acceptance

- Constituent/source metadata mandatory on every price
- 10–15 venues only (not 100)
- Not standalone — Oracle API layer only
