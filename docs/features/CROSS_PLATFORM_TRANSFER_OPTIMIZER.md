# Cross-Platform Transfer Optimizer — Feature #119 (Sprint 2)

## Purpose

Fee-saving route optimizer for moving assets between CEX platforms. **Not** a profit or arbitrage tool.

Integrated with:

- **#108** — Best transfer networks (speed / cost / security ranking)
- **#120** — User's saved network preference

## Example output

> To move USDT from Binance to Kraken, the optimal path is: Binance → BEP20 → Bridge → ERC20 → Kraken. Cost: $2.5. Duration: 4 minutes.

## API

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/transfer/optimizer` | Optimal cross-CEX route |
| `GET /api/platform/transfer/optimizer/status` | Feature metadata |
| `GET /api/platform/transfer/networks` | Network rankings (#108) |
| `GET/POST /api/platform/transfer/network-prefs` | User network (#120) |

### Query parameters (`/transfer/optimizer`)

- `asset` — USDT, USDC, ETH, BTC (default: USDT)
- `source_cex` — binance, kraken, okx, bybit, coinbase
- `dest_cex` — destination exchange
- `amount_usd` — transfer size for fee scoring
- `user_id` — optional, surfaces #120 preference comparison

## Logic

1. Enumerate direct routes (shared network on both CEX)
2. Enumerate bridged routes (withdraw network → bridge → deposit network)
3. Score by total cost (gas + bridge + withdrawal) and duration
4. Return headline, alternatives, alerts, disclaimer

## Acceptance

- Response ≤ 2 seconds
- Accuracy estimate ≥ 95% (fee estimates from gas oracle + static tables)
- No "profit" or "دورة ربحية" language
- User selects route — platform guarantees lowest **estimated** cost, not returns

## Disclaimer

BLACKDARK suggests routes based on public fee estimates. We do not execute transfers or guarantee delivery times. Verify withdrawal/deposit availability on each exchange before sending.
