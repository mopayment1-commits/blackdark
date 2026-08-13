# Four Remaining Blockers — Honest Status (post-external-action re-verify)

**Branch:** `cursor/95plus-recert-phase0-120d`  
**Evidence JSON:** `docs/dd/BLACKDARK_FOUR_BLOCKERS_EVIDENCE.json`  
**Integrity:** Never claim PASS / 100% / live execution / cloud HA without real evidence.

## Operator note

User marked both external actions complete in the Cloud UI. **Live re-probe from this
agent still fails** — UI completion alone is not evidence. Secrets remain present;
execution flags remain safe/disabled; prove uses scoped arming.

## Re-verify (this agent, egress `3.217.89.139`)

| Check | Observed |
|---|---|
| `testnet.binance.vision/api/v3/ping` | **HTTP 451** |
| `demo-api.binance.com/api/v3/ping` | **HTTP 451** |
| `api.binance.com/api/v3/ping` | **HTTP 451** |
| `data-api.binance.vision` ticker | HTTP 200 (market data only) |
| Wallet `BgaNfyoeqRtSF5ACHdz7sP1DqFa81Hj9XZ9dNLtB5Yf` | SOL lamports=**0**, USDC token accounts=**0** |
| Jupiter local sign | `signed_local=true` |
| Jupiter broadcast / VC | fail-closed `wallet_unfunded_zero_cost_constraint` |

## Blocker verdicts

| Blocker | Closed? | Status |
|---|---|---|
| Live venue FILL | **No** | Creds present; order hosts still **HTTP 451** → `live_fill=false` |
| Jupiter live signature VC | **No** | Local sign OK; wallet still unfunded → VC=false |
| Full Mesh institutional L2 100% | **No** | 52/100 venue_l2; 48 synthetic_mid |
| Cloud Multi-AZ HA | **No** | `zero_cost_no_paid_cloud_multi_az` (local streaming HA separate VC) |

## Acceptance criteria for the two external actions

1. **Binance geo:** From this Cloud Agent process,  
   `GET https://testnet.binance.vision/api/v3/ping` must return **HTTP 200**  
   (not 451). Then HMAC testnet order path can be re-proved for `live_fill`.
2. **Jupiter funding:** Wallet used by `SOLANA_PRIVATE_KEY` must show  
   `sol_lamports > 0` and/or USDC token account balance > 0 on mainnet RPC.  
   Exact current pubkey: `BgaNfyoeqRtSF5ACHdz7sP1DqFa81Hj9XZ9dNLtB5Yf`  
   (or re-inject a different funded `SOLANA_PRIVATE_KEY`).

## Absolute rule

`synthetic_mid` ≠ institutional L2.  
Local wallet sign ≠ RPC signature VC.  
Local streaming HA ≠ cloud multi-AZ.  
Paper / protocol fill ≠ `live_fill`.  
UI “action completed” ≠ observed network/wallet state.
