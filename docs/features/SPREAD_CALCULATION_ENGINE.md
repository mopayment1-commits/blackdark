# Spread Calculation Engine — Feature #427

## Decision

**Sprint-2 Core Economics Engine — merged into #429 Unified Arbitrage Engine, NOT standalone.**

| Requirement | Implementation |
|-------------|----------------|
| Decimal precision | `Decimal` throughout; `decimal_fields` in output |
| Synchronized timestamps | `timestamp_not_synchronized` reject if drift > 500ms |
| Fee/slippage included | `fee_matrix` fees + depth slippage in every net spread |
| Stale books rejected | `stale_book` fail-closed |
| Deterministic regression | 5 fixtures in seed |

## Formula

```
gross_spread_usdt = sell_notional − buy_notional   (depth-aware VWAP)
net_spread_usdt   = gross − trading_fees − slippage − transfer − withdrawal
net_spread_bps    = (net_spread_usdt / buy_notional) × 10,000
```

**Net spread is the only ranking standard** — gross spread alone is never used for opportunity ranking.

## Output

- `gross_spread_bps` / `gross_spread_usdt`
- `net_spread_bps` / `net_spread_usdt`
- `executable_size`
- `source_venues` (buy + sell)
- `rejection_reason` when fail-closed

## Routes (via #429)

```
GET /api/platform/intelligence-ledger/unified-arbitrage/economics/status
GET /api/platform/intelligence-ledger/unified-arbitrage/economics/regression
GET /api/platform/intelligence-ledger/unified-arbitrage/economics/reconciliation-tests
```

## Integrations

- **#429** — all arbitrage types use `compute_arbitrage_economics()` / `compute_cross_venue_spread()`
- **#415** — depth books for executable pricing
- **fee_matrix** — venue trading + withdrawal fees
