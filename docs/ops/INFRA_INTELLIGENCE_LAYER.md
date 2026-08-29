# Infrastructure & Intelligence Layer (#95–#104)

## #95 Feature Usage Analytics

`GET /admin/analytics` (admin + MFA)

Internal-only dashboard. Rule-based event tracking on every endpoint. GDPR-compliant, no third-party tracking.

## #96 Streaming Stack

`GET /api/platform/data-engine/streaming/status`

Merged into Data Engine. Redis Streams transport. AI training deferred — architecture ML-ready.

## #97 Data Flywheel

`POST /api/platform/intelligence/feedback`

Feedback loop in Intelligence Ledger. Hit/Miss/Neutral → weight update → improved scoring.

## #98 Sovereign Signal Registry

`GET /api/platform/registry/status`

Unified signal definitions. CI blocks duplicate logic with different names.

## #99 Sybil Attack Density Filter

`GET /radar/sentiment/filter` · `GET /oracle/on-chain/filter`

Rule-based cluster detection. Excludes suspicious wallets from sentiment/on-chain metrics.

## #100 Liquidation Cascade Proximity

Merged into #82 (`/radar/alerts/liquidation`). Proximity metric dimension added.

## #101 Oracle Latency Deviation Buffer

`GET /oracle/validate`

Stale data rejection: >5s stale, >15s critical. Every response includes `data_freshness_ms`.

## #102 Impermanent Loss Vulnerability Score

`GET /oracle/on-chain/defi/il-score`

DeFi IL formula + volatility + liquidity depth → score 0–100.

## #103 Max Drawdown Duration

Merged into #77 Advanced Risk Tab. Peak/trough/recovery lifecycle.

## #104 Leverage Ratio Overhang Factor

`GET /radar/market-health`

Overhang = (OI × Avg Leverage) / Spot Liquidity. Red >3.0, Yellow 2.0–3.0.

## E2E

```
GET /api/platform/infra-intelligence/e2e  (admin)
pytest tests/test_infra_intelligence_batch95_104.py -q
```
