# BLACKDARK INSTITUTIONAL COMPLETION REGISTER

**PR:** #72  
**Branch:** `cursor/95plus-recert-phase0-120d`  
**Tip:** `ac13c0ef7fdde8414906b45155001390255d8485`  
**Rule:** Register never exceeds independent clean-room classifications.

## Latest implementation (awaiting / bound by clean-room)

| Priority | Deliverable | Pre-clean-room class | Evidence |
|---|---|---|---|
| C1 | Venue L2 on Canonical Truth Bus (no fabricated 2.0+i sizes) | PARTIAL→stronger PARTIAL | `live_data_truth_probe` OKX books + Kraken Depth; `canonical_truth_bus` |
| C2 | Fill proof walks venue L2 depth; live_fill honest | PARTIAL (paper) | `venue_fill_proof.py` |
| C3 | Venue perpetual books + venue funding into Super Terminal | PARTIAL | OKX perp+funding via aggregator → bus → `_derivatives_pack` |
| C4 | Durable ingestion_source_health rows | PARTIAL | `institutional_ingestion_proof.prove_durable_ingestion` |
| C5 | Ops schema authority (SQLite/Postgres engine) | PARTIAL | `ops_recovery.prove_db_authority_tables` |

## Binding clean-room

Prior binding tip `3c01c26` / intermediate `3981914`: **70/100 NOT COMPLETE**, VERIFIED_COMPLETE **0**.  
New tip `ac13c0e` clean-room supersedes when the independent audit file lands.

## Absolute rule

Green tests / HARDENED / self-`product_complete` ≠ COMPLETE.
