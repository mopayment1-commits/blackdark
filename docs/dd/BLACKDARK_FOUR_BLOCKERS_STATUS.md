# Four Remaining Blockers — Honest Status (operator skipped external unblock)

**Branch:** `cursor/95plus-recert-phase0-120d`  
**Evidence JSON:** `docs/dd/BLACKDARK_FOUR_BLOCKERS_EVIDENCE.json`  
**Integrity:** Never claim PASS / 100% / live execution / cloud HA without real evidence.

## Operator decision (this wave)

Operator **skipped**:
1. Binance order-host geo unblock (HTTP 451 still observed from this agent)
2. Jupiter wallet funding / funded-key re-inject
3. Optional `HTTPS_PROXY` / `HTTP_PROXY` / `ALL_PROXY` / funded `SOLANA_PRIVATE_KEY`

Those are now **accepted external blocks**. Secrets already in this agent remain present
(`BINANCE_API_KEY`/`SECRET`, `SOLANA_PRIVATE_KEY`); live flags stay safe/disabled;
prove paths use scoped arming only. Product verdict: **NOT COMPLETE**.

## Frozen observed state

| Surface | Evidence |
|---|---|
| Live venue FILL | `live_fill=false`; `binance_order_host_geo_451` |
| Jupiter | `signed_local=true`; `wallet_unfunded_zero_cost_constraint`; VC=false |
| Full Mesh institutional L2 | 52/100 `venue_l2`; 48 `synthetic_mid`; CORE 60/60 live L2 |
| Cloud multi-AZ HA | `zero_cost_no_paid_cloud_multi_az` |
| Local Postgres streaming HA | `verified_complete=true` (not cloud multi-AZ) |

## What remains closed without payment

- HMAC fill path + geo probe honesty (creds present; no fake fill)
- Jupiter quote/build/local wallet sign + unfunded fail-closed classification
- Catalog price health 100% with depth labels
- CORE public mesh 60/60 live L2
- Local streaming HA VC

## Absolute rule

`synthetic_mid` ≠ institutional L2.  
Local wallet sign ≠ RPC signature VC.  
Local streaming HA ≠ cloud multi-AZ.  
Paper / protocol fill ≠ `live_fill`.  
Operator skip ≠ product PASS.
