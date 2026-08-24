# On-Chain Address Intelligence Module — Features #10 + #19 + #20

Unified module (NOT three separate product surfaces):

| # | Capability | Function | API |
|---|------------|----------|-----|
| 10 | Address Search | `search_address()` | `GET /api/platform/address-intelligence/search` |
| 19 | Balance History Chart | `balance_history()` | `GET /api/platform/address-intelligence/history` |
| 20 | Balance Updates (state diffs) | `balance_updates()` | `GET /api/platform/address-intelligence/updates` |

Unified overview: `GET /api/platform/address-intelligence/overview`

## Data sources

- Tracely (free fallback)
- DeBank / Zerion (when API keys configured)
- eth-labels.com
- Arkham entity intelligence (when `ARKHAM_API_KEY` set)

## Balance history (#19)

Snapshots stored in `data/address_balance_snapshots.jsonl` with chain-specific keys.
Proxy bootstrap disclosed when insufficient snapshot history exists.

## Balance updates (#20)

State-diff feed computed from consecutive snapshots:
- `delta_usd`, `delta_pct`, `direction` (inflow/outflow/unchanged)
- Chain-specific correctness via `chain` + `chain_id` fields

## Acceptance criteria

| Criterion | Target |
|-----------|--------|
| Chain-specific correctness | `chain` + `chain_id` on all responses |
| API latency | ≤2s per capability (`sla_met`) |
| Real-time updates | Snapshot diff on each poll |

## UI

`/address-intelligence` — Search, History Chart, Balance Updates tabs
