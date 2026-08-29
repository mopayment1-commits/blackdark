# Security, Trust & Data Sources Layer (#242–#261)

## #242 Audit Trail

`POST /audit/log` · `GET /audit/export` (admin MFA) — immutable append-only chain-of-hashes log.

## #243 Bybit API

Merged into Oracle — `GET /oracle/prices/bybit` secondary fallback source.

## #244 CoinTelegraph RSS

`GET /radar/news/cointelegraph` — merged into Market Radar.

## #245 CoinMarketCal

Merged into `/radar/events` — activation only (existing calendar endpoint).

## #246 Etherscan Watch List

`GET/POST /oracle/on-chain/watch` — manual address monitoring, privacy-first.

## #247 Weekly Digest

`GET /intelligence/weekly-digest` — rule-based weekly report in Intelligence Ledger.

## #248 Profit Analytics — REJECTED

Alternative: `GET /portfolio/performance/manual` — manual performance tracker.

## #249 TRAD Simulator — REJECTED

No module — use Backtest (#74).

## #250 Execution Speed — REJECTED

No build in any sprint.

## #251 Token Velocity

`GET /oracle/on-chain/token-velocity`

## #252 Google Trends

`GET /radar/sentiment/google-trends`

## #253 Kill-Rate Board

`GET /public/kill-rate` — Proof Arena widget.

## #254 Contradiction Replay

`GET /proof-arena/contradiction-replay`

## #255 Committee One-Pager

Merged into Intelligence Ledger — Pro/Desk tier.

## #256 Half-Life Heat Clock

Merged into Signal Engine — component data.

## #257 Proof Arena Lite

Merged into Proof Arena — mode: lite.

## #258 Since You Left

`GET /portfolio/since-you-left`

## #259 Anti-Hype Mode

`POST /settings/anti-hype` — user preference dictionary.

## #260 Corpus Passport

Merged into Intelligence Ledger — requires Audit Trail #242.

## #261 Pricing Model

`GET /stripe/tiers` — extends #60: Proof/Pro/Desk/Data Room.

## E2E

```
GET /api/platform/security-trust-data/e2e  (admin)
pytest tests/test_security_trust_data_batch242_261.py -q
```
