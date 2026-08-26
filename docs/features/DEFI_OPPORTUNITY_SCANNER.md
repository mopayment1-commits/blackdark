# DeFi Opportunity Scanner Merges — #465, #470, #473 → #438

## Summary

Three DeFi features merged into **#438 DeFi Opportunity Scanner** — no standalone modules.

| Feature | Legal Name | Merged Into |
|---------|------------|-------------|
| #465 | DEX Screener | #438 |
| #470 | LP Position Risk Calculator | #438 (renamed from IL Live Simulator) |
| #473 | Liquidity Risk | #438 |

---

## #465 DEX Screener

- **4 DEXs v1:** Uniswap, PancakeSwap, Raydium, Jupiter
- **Pool mapping** across DEXs per pair
- **Honeypot:** honeypot.is API (no internal detector v1)
- **Risk flags:** contract verified, liquidity locked, owner renounced, tax token
- **Default filters:** liquidity > $100K, volume 24h > $10K, age > 7 days

---

## #470 LP Position Risk Calculator

Renamed from "Impermanent Loss Live Simulator".

| Input | Output |
|-------|--------|
| Pair assets, entry/current prices | IL estimate % |
| Pool ratio, fees APY, days held | Fee offset USD |
| — | Net PnL USD |
| — | Collateral grade (#462 integration) |

Cancelled SLA: ≤2s response, ≥95% accuracy, 99% uptime, real-time update.

---

## #473 Liquidity Risk

**6 protocols v1:** Aave, Compound, Uniswap, Curve, Lido, Maker

| Indicator | Description |
|-----------|-------------|
| TVL trend | 7-day % change |
| Utilization rate | Pool utilization |
| Borrow/supply ratio | Lending market health |
| Liquidation threshold | Protocol-specific |

- Update every 15 minutes (data quality standard)
- Accuracy ±0.1%
- Historical ≥1 year
- Liquidity risk score affects collateral grade (#462)

---

## Routes

```
GET /api/platform/intelligence-ledger/unified-arbitrage/defi
GET /api/platform/intelligence-ledger/unified-arbitrage/defi/status
GET /api/platform/intelligence-ledger/unified-arbitrage/defi/dex-screener
GET /api/platform/intelligence-ledger/unified-arbitrage/defi/lp-position-risk
GET /api/platform/intelligence-ledger/unified-arbitrage/defi/liquidity-risk
GET /api/platform/intelligence-ledger/unified-arbitrage/defi/reconciliation-tests
```

---

## Tests

```
12 passed — tests/test_defi_opportunity_scanner_batch.py
```
