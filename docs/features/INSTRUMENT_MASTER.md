# Instrument Master & Coverage Expansion — #268 (Sprint 1 Data Engine)

**NOT standalone** — merged into **Wave 01 Data Engine** as Instrument Master & Coverage Expansion.
Standalone ticket #268 archived. Marketing claim of 1.3M instruments replaced with validated crypto-native ~50K.

## Institutional Decision

| Aspect | Decision |
|--------|----------|
| Standalone #268 | ❌ Archived |
| Merge target | Wave 01 Data Engine (Sprint 1) |
| Product | Mapping quality, not volume |
| TradFi/equities | Wave 3 — out of scope |

## Scope Lock

```
1.3M instruments: crypto spot + perps + options only | TradFi/equities = Wave 3 |
Source: [CEX APIs + DEX on-chain + derivatives venues] |
Update: real-time for top 5K, delayed for remainder
```

## Instrument Mapping Schema

| Field | Description |
|-------|-------------|
| Instrument ID | UUID |
| Venue | CEX / DEX / Derivatives |
| Asset class | spot / perp / option |
| Base/quote | Normalized pair |
| Mapping confidence | 0–100% |
| Last verified | Timestamp |
| Rule | No mapping = no ingestion |

## Deduplication

Reuses existing Sprint 1 tables — **no duplicate pipelines**:

- `data_sources`
- `ohlcv_data`
- `market_snapshots`
- `funding_rates`
- `open_interest`
- `ingestion_runs`

## Cost Gate

| Tier | Share | Policy |
|------|-------|--------|
| Hot | 5% | Active — real-time |
| Warm | 15% | Monitor — delayed |
| Cold | 80% | Archive — auto-archive < $1K daily after 90 days |

## Acceptance Criteria

| Criterion | Target |
|-----------|--------|
| Instrument mappings | Required |
| Latency SLA (top 5K) | < 500ms |
| Coverage accuracy | > 99% vs CoinGecko |
| Uptime SLA | 99.9% |
| Provenance per tick | Source tagging required |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/data/instrument-master/status` | Module status |
| `GET /api/v1/data/instrument-master/mappings` | List mappings (filter by tier/class) |
| `GET /api/v1/data/instrument-master/mappings/{id}` | Single instrument mapping |
| `GET /api/v1/data/status` | Includes `instrument_master_268` summary |

## Related

- `blackdark/data/instrument_master.py` — core module
- `data/instrument_master_seed.json` — validated instrument registry
- `WAVE_01_DATA_ENGINE.md` — parent Data Engine documentation
