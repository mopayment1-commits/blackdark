# DeFi TVL + Canonical Assets + Yield Sustainability — #702, #705, #709

## #702 — DeFi TVL Engine (Sprint 2 — DeFi Core)

Market Radar DeFi layer with normalized TVL.

| Rule | Implementation |
|------|----------------|
| Double-count policy | `Aave TVL includes borrowed tokens — we exclude them` |
| Methodology versioned | `v2.1: staking tokens counted separately` |
| Source metadata | `Source: DeFiLlama \| URL` per protocol |

### APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/market-radar/defi/tvl` | TVL dashboard |
| `GET /api/platform/market-radar/defi/tvl/{id}` | Protocol detail |
| `GET /api/platform/market-radar/defi/tvl/methodology` | Methodology + policy |
| `GET /api/platform/market-radar/defi/tvl/status` | Module status |

---

## #705 — Tokenized Asset Coverage → #194 Unified Connector (merged)

**NOT standalone** — metadata layer with stable IDs + lifecycle versioning.

| Rule | Implementation |
|------|----------------|
| Stable IDs | `asset:eth:ethereum` everywhere |
| Lifecycle | `active`, `deprecated`, `dead` |
| Symbol chaos prevention | `ETH` = canonical, `ETH-OLD` = legacy |

### APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/connectors/assets` | Canonical asset list |
| `GET /api/platform/connectors/assets/resolve/{symbol}` | Symbol → stable ID |
| `GET /api/platform/connectors/unified` | Coverage + assets (#194+#705) |

---

## #709 — Yield History → Yield Sustainability Score (merged #198 + #710)

| Rule | Implementation |
|------|----------------|
| Yield display | `Current APY: 12% \| 30-day avg: 11.8% (stable)` |
| Incentive decomposition | `70% fees, 30% temporary incentives` |
| Sustainability | `🟢 High` / `🟡 Medium` / `🔴 Critical` |
| Outlier detection | Volatile APY flagged as red flag |
| Time-series stability | std dev + history analysis |

### APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/defi/yield-sustainability` | Pool sustainability scores |
| `GET /api/platform/defi/yield-sustainability/{id}` | Pool detail + 30d history |
| `GET /api/platform/defi/yield-sustainability/status` | Module status |

## Related

- `bd_platform/connector_coverage_map.py` — #194 Unified Connector
- `bd_platform/incentive_tracker.py` — #203 incentive programs
- `bd_platform/free_tier_capabilities.py` — DeFiLlama yield data
