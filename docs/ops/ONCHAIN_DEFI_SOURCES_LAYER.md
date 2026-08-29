# On-Chain, DeFi & Arbitrage Sources Layer (#204–#216)

## #204 BscScan API

`GET /oracle/on-chain/bsc` — BSC transactions, balances, token transfers with RPC cross-validation. BEP-20 ≠ ERC-20 documented.

## #205 Glassnode Studio

`GET /oracle/on-chain/sources/glassnode` — free-tier NUPL, SOPR, MVRV mapped to Sovereign Signal Registry (#98).

## #206 Uniswap Subgraph

`GET /oracle/on-chain/defi/uniswap` — pools, swaps, liquidity, volume via GraphQL.

## #207 Aave API/Subgraph

`GET /oracle/on-chain/defi/aave` — lending rates, borrowing rates, TVL, liquidations.

## #208 Reddit API

`GET /radar/sentiment/social/reddit` — r/CryptoCurrency posts with keyword extraction and deduplication.

## #209 Blockchain.com Wallets — merged #148

Activation only — no duplicate build. Covered by `/oracle/on-chain/sources/blockchain-com`.

## #210 Predictive Arbitrage — extends #153

`GET /intelligence/arbitrage/predictive` — rule-based historical pattern matching, embedded in Arbitrage Engine.

## #211 Cross-Margin Risk Alert — safeguard rejected

`GET /portfolio/cross-margin-risk` — insight-only risk score and contagion vector. No safeguard or execution.

## #212 Dynamic Re-hedging — REJECTED

Alternative: `GET /portfolio/hedge-analysis` — hedge effectiveness simulation only.

## #213 Auto-Balancing — REJECTED

Alternative: `GET /portfolio/capital-allocation` — capital allocation insight only.

## #214 Triangular Arbitrage In-Flight — REJECTED

Alternative: embedded in #153 as `triangular_analysis` — path comparison only.

## #215 Flash Loan Gas — REJECTED

Alternative: Gas Optimization Insight (#159).

## #216 Whale Counter-Trading — REJECTED

Alternative: embedded in Whale Narrative (#71) as `contrarian_insight`.

## E2E

```
GET /api/platform/onchain-defi-sources/e2e  (admin)
pytest tests/test_onchain_defi_sources_batch204_216.py -q
```
