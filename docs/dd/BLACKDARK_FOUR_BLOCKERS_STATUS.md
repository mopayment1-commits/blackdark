# Four Remaining Blockers — Honest Status

**Branch:** `cursor/95plus-recert-phase0-120d`  
**Evidence JSON:** `docs/dd/BLACKDARK_FOUR_BLOCKERS_EVIDENCE.json`  
**Integrity:** Never claim PASS / 100% / live execution / cloud HA without real evidence.

## Runtime secrets in this Cloud Agent

At evidence collection time, `BINANCE_API_KEY`, `BINANCE_API_SECRET`, `SOLANA_PRIVATE_KEY`,
`JUPITER_LIVE_EXECUTION`, `BINANCE_TESTNET`, `AUTO_EXECUTION_ENABLED`, and
`AUTO_EXECUTION_DRY_RUN` were **absent** from the process environment (lengths 0), despite
operator statement that Runtime Secrets were added. Remediation code is landed; live proves
that require secrets remain blocked until secrets are injected into **this** run.

## 1) Live venue FILL

| Field | Status |
|---|---|
| Code path | Armed prove + testnet env-operator exception (non-prod) + order-host geo probe |
| `live_fill` | **false** |
| External block | **`binance_order_host_geo_451`** — `testnet.binance.vision` / demo-api / api.binance.com return HTTP 451 from this egress |
| Market data | `data-api.binance.vision` works (books only) — does **not** authorize fills |
| Closure | **Externally blocked** (geo). Also secrets not injected into this run. |

## 2) Jupiter live signature

| Field | Status |
|---|---|
| Code path | `prove_jupiter_wallet_sign` (local sign + optional RPC broadcast) |
| Local sign | Requires `SOLANA_PRIVATE_KEY` in runtime (absent here) |
| On-chain VC | Requires funded wallet + RPC-accepted signature |
| External block | **`wallet_secret_absent_in_runtime`** now; with key present but unfunded → `wallet_unfunded_zero_cost_constraint` |
| Closure | **Externally blocked** (secrets injection + zero-cost unfunded wallet). |

## 3) Full Mesh 100%

| Field | Status |
|---|---|
| Catalog price health | **100%** (includes honest `synthetic_mid`) |
| Institutional L2 | **~46%** (`venue_l2≈46/100`) |
| CORE public L2 mesh | **52/52** live L2 (includes Binance via vision) |
| `full_mesh_l2_complete` | **false** |
| External block | **`geo_dead_or_no_public_l2_for_remaining_venues`** |
| Closure | **Not closed** — cannot fabricate L2 for dead/geo venues. |

## 4) Cloud Multi-AZ HA

| Field | Status |
|---|---|
| `prove_cloud_multi_az_ha` | `cloud_multi_az=false` |
| External block | **`zero_cost_no_paid_cloud_multi_az`** |
| Local streaming HA | Still **VERIFIED_COMPLETE** separately (`cloud_multi_az=false`) |
| Closure | **Externally blocked** (paid cloud not authorized). |

## What was remediable without cost / secrets

1. Testnet env-operator allow (non-production only) so vault gate does not block Spot Testnet proves.
2. Binance order-host connectivity prove with honest 451 classification.
3. Fill prove arming + geo fail-closed (never claims `live_fill` on 451).
4. Jupiter wallet-sign prove surface (local vs RPC signature separation).
5. Institutional L2 metric separated from catalog price-health %.
6. CORE mesh includes Binance vision L2 (52 targets).
7. Explicit cloud multi-AZ prove that refuses theater under zero-cost policy.
