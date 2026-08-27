# Feature #43 — Cross-Chain Data Warehouse

Backend database layer unifying multi-chain datasets under canonical schema (#29 + #16).

## Principles

- **NOT** a user-facing UI
- Serves On-Chain Module, explorer, and analytics
- Chain semantics documented per chain (address format, finality, value fields)

## Storage

- SQLite: `data/warehouse/cross_chain_warehouse.db`
- Tables: `warehouse_chains`, `warehouse_transactions`, `warehouse_balances`
- JSONL index fallback via `transaction_index.py`

## APIs (infrastructure)

| Endpoint | Purpose |
|----------|---------|
| `GET /api/platform/warehouse/cross-chain/status` | Warehouse health |
| `GET /api/platform/warehouse/cross-chain/semantics` | Chain semantics registry |
| `GET /api/platform/warehouse/cross-chain/transactions` | Warehouse query access |

## Integration

- `cross_chain_explorer.py` mirrors indexed txs into warehouse on fetch
- Uses `NormalizedTransaction` from `blackdark/canonical/cross_chain_schema.py`
- Resolves `canonical_asset_id` via `resolve_asset()`

## Supported chains (semantics documented)

ethereum, bsc, arbitrum, polygon, solana, tron, avalanche, optimism
