# On-Chain Address Intelligence Module — Features #10 + #18 + #19 + #20 + #23

Unified module (NOT separate product surfaces):

| # | Capability | Function | API |
|---|------------|----------|-----|
| 10 | Address Search (point-in-time) | `search_address()` | `GET /api/platform/address-intelligence/search` |
| 18 | Fund Trace (single-chain) | `trace_funds()` | `GET /api/platform/address-intelligence/trace` |
| 19 | Balance History Chart | `balance_history()` | `GET /api/platform/address-intelligence/history` |
| 20 | Balance Updates (state diffs) | `balance_updates()` | `GET /api/platform/address-intelligence/updates` |
| 23 | Block Search (explorer) | `search_block()` | `GET /api/platform/address-intelligence/block` |

Unified overview: `GET /api/platform/address-intelligence/overview`

Point-in-time balance: `GET /api/platform/address-intelligence/balance-at?as_of=ISO8601`

## Point-in-time semantics (#10, #19)

`bd_platform/address_state_index.py` provides block-anchored queries:

1. **Etherscan archive** (when `ETHERSCAN_API_KEY` set): `getblocknobytime` → balance at block
2. **Local snapshot index**: nearest snapshot ≤ `as_of`
3. **Live fallback** (disclosed): when no historical anchor exists

Reorg handling: recent blocks may be marked `finalized: false` with `reorg_risk` disclosure.

## Block search (#23)

`search_block()` in `address_intelligence.py` — block explorer index/query merged into this module:

- `bd_platform/onchain_client.py` — `get_block_by_number()` with Etherscan + RPC fallback
- Normalized fields: `block_number`, `hash`, `parent_hash`, `timestamp`, `tx_count`, `gas_used`
- Reorg/finality: `finalized`, `reorg_risk`, `confirmations` on every response
- API: `GET /api/platform/address-intelligence/block?block_number=&chain=ethereum`

## Fund trace (#18)

`bd_platform/fund_trace.py` — single-chain Ethereum MVP:

- Graph built from verified Etherscan transactions only
- `fabricated: false` always
- Bridge contracts labeled `bridge_exit` — **no cross-chain path inference**
- BFS path search with configurable `max_hops`

## Data sources

- Tracely (free fallback)
- DeBank / Zerion (when API keys configured)
- eth-labels.com
- Arkham entity intelligence (when `ARKHAM_API_KEY` set)
- Etherscan (when `ETHERSCAN_API_KEY` set) — block anchoring + trace

## Balance history (#19)

Snapshots stored in `data/address_balance_snapshots.jsonl` with chain-specific keys.
Each point carries `semantics: point_in_time` and optional `block_number`.
Proxy bootstrap disclosed when insufficient snapshot history exists.

## Balance updates (#20)

State-diff feed computed from consecutive snapshots:
- `delta_usd`, `delta_pct`, `direction` (inflow/outflow/unchanged)
- Chain-specific correctness via `chain` + `chain_id` fields

## Acceptance criteria

| Criterion | Target |
|-----------|--------|
| Point-in-time semantics | Block or snapshot anchor on all historical queries |
| Reorg handling (#23) | `finalized` / `reorg_risk` disclosure on block queries |
| Chain-specific correctness | `chain` + `chain_id` on all responses |
| No fabricated trace paths | Only verified tx edges (#18) |
| Bridge handling | Explicit labels; no cross-chain inference in MVP |
| API latency | ≤3s per capability (`sla_met`) |
| Real-time updates | Snapshot diff on each poll |

## UI

`/address-intelligence` — Search, History Chart, Balance Updates tabs
