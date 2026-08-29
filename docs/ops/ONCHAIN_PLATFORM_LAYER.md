# On-Chain Platform Layer (#129–#139)

## #129 Sybil Identity Linker

`POST /oracle/on-chain/sybil-clustering` — extends #99 with entity clustering.

## #130 Shadow-Fork — REJECTED

Alternative: `GET /oracle/on-chain/tx-risk` — transaction risk insight.

## #131 Dust Sweeper — REJECTED

Alternative: `GET /portfolio/dust-analysis` — dust asset analysis.

## #132 Flash Loan Scanner

`GET /oracle/on-chain/security/flash-loan-scan` — no self-patching.

## #133 Macro Event Nexus

Merged into Multi-Dim (#73) + `/radar/market-health/macro` — rule-based.

## #134 Delta Convergence

`GET /radar/derivatives/delta-convergence` — Pro/Institution tier.

## #135 Liquidity Vortex

`GET /radar/market-health/liquidity-vortex` — rule-based pattern detection.

## #136 Support Chatbot

`POST /support/chat` — FAQ only, broker-advisor rejected.

## #137 B2B Relationships — NOT TECHNICAL

Business development activity — Wave 3, no code module.

## #138 Institutional Features — Wave 3 Activation

Activation of existing bundle (#87, #85, #136, #89, #88).

## #139 Panic Button — REJECTED

Alternative: `GET /portfolio/stress-alert` — proactive stress insight.

## E2E

```
GET /api/platform/onchain-platform/e2e  (admin)
pytest tests/test_onchain_platform_batch129_139.py -q
```
