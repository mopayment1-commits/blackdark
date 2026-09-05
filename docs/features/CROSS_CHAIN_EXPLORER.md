# Unified Cross-Chain Explorer — Features #101 + #103 + #100

## #101 Transaction Search / Unified Cross-Chain Explorer

**Sprint 1 Core Infrastructure** — one address, all chains, one page.

| Component | Path |
|-----------|------|
| Explorer | `bd_platform/cross_chain_explorer.py` |
| Index | `bd_platform/transaction_index.py` |
| Schema | `blackdark/canonical/cross_chain_schema.py` |

### APIs

- `GET /api/platform/cross-chain/explorer?address=` — unified assets + txs (Ethereum, BSC, Arbitrum, Polygon, Solana, Tron)
- `GET /api/platform/transactions/search?address=&chain=&cursor=&limit=` — indexed search with cursor pagination

### Acceptance

- Query correctness: stable sort `(timestamp DESC, chain, tx_hash)`
- Pagination: cursor-based, tested on 100k+ row index
- Chain/time semantics: `start_time` / `end_time` unix filters, per-chain registry

## #103 Tronscan (Unified Connector #194)

- `blackdark/ingestion/tronscan_connector.py` via `unified_connector.py`
- Normalized to `cross_chain_schema`
- Fallback: TronGrid → stale cache
- NOT branded — feeds cross-chain explorer silently

## #100 Transaction Decoder (AI Layer)

- `bd_platform/transaction_decoder.py`
- `GET /api/platform/transactions/decode?tx_hash=&chain=`
- Known selectors verified from calldata; unknown actions marked
- `intent_inferred: false` always — no hallucinated intent

### Example

*"AI Decoded: This transaction is a liquidity provision to Uniswap V3 pool. You may earn trading fees. Risk: impermanent loss."*
