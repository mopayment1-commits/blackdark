# Feature #78 — Network Growth Intelligence

Silent Decision Engine metric measuring first-seen addresses interacting with an asset.

## Scope

**NOT a standalone product** — feeds #48 Decision Engine with growth + acceleration (second derivative).

## First-seen logic

- Immutable `first_seen_ts` per `chain:address` in `data/network_address_first_seen.json`
- Ingest from `cross_chain_tx_index.jsonl` + cross-chain warehouse transfers
- Prototype synthetic transfers when live index is sparse (deterministic, documented)

## Spam/dust policy

| Rule | Default |
|------|---------|
| Min transfer USD | $10 |
| Dust max USD | $1 (always excluded) |
| Min interactions | 3 (unless total USD ≥ min transfer) |
| Internal exchange hops | Filtered via exchange flow labels |
| Reorg handling | First-seen timestamp never reset |

## Metrics

- `new_addresses_1d` / `new_addresses_7d`
- `acceleration_pct` — week-over-week growth derivative
- `growth_index` — normalized adoption index

## APIs

| Endpoint | Purpose |
|----------|---------|
| `GET /api/platform/network-growth/analyze?asset=SOL` | Full snapshot |
| `GET /api/platform/network-growth/status` | Module health |
| `decision_engine_inputs.network_growth` | Compact risk feed |

## User headline example

*"SOL network growth accelerated 45% this week — historically correlated with elevated price moves within 14 days"*
