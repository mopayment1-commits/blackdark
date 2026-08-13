# Four Remaining Blockers — Honest Status (secrets-injected wave)

**Branch:** `cursor/95plus-recert-phase0-120d`  
**Evidence JSON:** `docs/dd/BLACKDARK_FOUR_BLOCKERS_EVIDENCE.json`  
**Integrity:** Never claim PASS / 100% / live execution / cloud HA without real evidence.

## Operator constraint (this wave)

Runtime secrets were injected into **this** agent (free): `BINANCE_API_KEY`,
`BINANCE_API_SECRET`, `SOLANA_PRIVATE_KEY`, plus flags
`BINANCE_TESTNET`, `AUTO_EXECUTION_*`, `JUPITER_LIVE_EXECUTION`.

Flags arrived safe/disabled (`AUTO_EXECUTION_ENABLED=false`,
`AUTO_EXECUTION_DRY_RUN=true`, `JUPITER_LIVE_EXECUTION=false`). Prove paths use
**scoped arming** only when credentials are present — never invent wallets or
keys. Zero-cost: no funded SOL/USDC, no paid cloud multi-AZ.

## What closed without payment (secrets wave)

| Deliverable | Evidence |
|---|---|
| HMAC fill path armed with real Binance creds | `has_creds=true`; live path armed under testnet scope |
| Order-host geo probe (honest) | `testnet.binance.vision` + `demo-api.binance.com` → **HTTP 451** |
| Jupiter local wallet sign | `signed_local=true` pubkey `BgaNfyoeqRtSF5ACHdz7sP1DqFa81Hj9XZ9dNLtB5Yf` |
| Jupiter broadcast fail-closed | RPC sim `AccountNotFound`; SOL=0, USDC accounts=0 |
| Unfunded classification | `external_block=wallet_unfunded_zero_cost_constraint` |
| CORE public mesh | **60/60** live L2 |
| Catalog price health | **100%** with depth labels (`venue_l2` vs `synthetic_mid`) |
| Institutional L2 catalog | **52/100** venue_l2; 48 synthetic_mid (not claimed as L2) |
| Local Postgres streaming HA | `verified_complete=true` (not cloud multi-AZ) |

## Blocker verdicts (post-secrets evidence)

| Blocker | Closed? | Status |
|---|---|---|
| Live venue FILL | **No** | Creds present + path armed; order hosts **HTTP 451** → `binance_order_host_geo_451`; `live_fill=false` |
| Jupiter live signature VC | **No** | Local sign proven; broadcast blocked as `wallet_unfunded_zero_cost_constraint`; `verified_complete=false` |
| Full Mesh institutional L2 100% | **No** | 52/100 venue_l2; remaining `geo_dead_or_no_public_l2_for_remaining_venues` |
| Cloud Multi-AZ HA | **No** | `zero_cost_no_paid_cloud_multi_az` (local streaming HA is separate VC) |

## Absolute rule

`synthetic_mid` ≠ institutional L2.  
Local wallet/ephemeral sign ≠ RPC signature VC.  
Local streaming HA ≠ cloud multi-AZ.  
Paper / protocol fill ≠ `live_fill`.  
Geo 451 / unfunded wallet / unpaid cloud are **external blocks**, not product PASS.
