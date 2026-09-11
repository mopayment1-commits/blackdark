# Batch 06 Run 015 — RBAS-001 Opening Diagnostic Report (IDs 251–300)

**Generated:** 2026-09-11T09:29:30.547071+00:00  
**Run:** Master Contract 015  
**Policies:** RBAS-001 | RTM-IND-001 | SCORE-IDX-001 | CROSS-SPINE-001 | WF-027  

## Item 1 — WF-027 Preflight (mandatory first)

- **WF-027 historical set (10 IDs):** `[175, 214, 245, 584, 629, 630, 631, 642, 644, 646]`
- **Resolved prior (Batch04/05):** `[175, 214, 245]`
- **Unresolved remaining (7 IDs):** `[584, 629, 630, 631, 642, 644, 646]`
- **Batch06 official range:** 251-300
- **Intersection (overlap):** `[]` — **0/7** unresolved IDs
- **Live rg scan:** `rg -n '584|629|630|631|642|644|646' cap646/batch01_production.py scripts/rbas001_scoping.py` → exit 0
- **Python set intersection:** `[]` (empty = zero overlap confirmed)
- **Preflight evidence:** WF-027 unresolved=[584, 629, 630, 631, 642, 644, 646]; Batch06 range 251-300; intersection=[] (0/7 unresolved WF-027 IDs in scope). 175/214/245 resolved in Batch04/05.

## Item 2 — Pre-Audit Tier Classification (50/50)

- **Tier1:** 17/50 (full nine-phase)
- **Tier2:** 33/50 (abbreviated path)

See `RBAS001_TIER_CLASSIFICATION_BATCH06.json` for per-ID reasons.

### Tier Table Summary

| ID | Capability | Tier | Reason |
|---:|---|---|---|
| 251 | Cross-Domain Decision Intelligence | **TIER1** | Cross-Domain Decision Intelligence — explicit decision output |
| 252 | Liquidation Heatmap | **TIER2** | Liquidation Heatmap — liquidation metric delivery |
| 253 | Liquidation Map / Levels | **TIER2** | Liquidation Map / Levels — liquidation level delivery |
| 254 | Real-Time Liquidation Events | **TIER2** | Real-Time Liquidation Events — event feed delivery |
| 255 | Open Interest Intelligence | **TIER2** | Open Interest Intelligence — metric delivery (duplicate_of=205) |
| 256 | Funding Rate Intelligence | **TIER2** | Funding Rate Intelligence — metric delivery (duplicate_of=86) |
| 257 | Long/Short Ratio Intelligence | **TIER2** | Long/Short Ratio Intelligence — ratio metric delivery (duplicate_of=235) |
| 258 | Top Trader Positioning | **TIER2** | Top Trader Positioning — positioning metric delivery |
| 259 | Futures Basis Intelligence | **TIER2** | Futures Basis Intelligence — basis metric delivery |
| 260 | Futures Volume Intelligence | **TIER2** | Futures Volume Intelligence — volume metric delivery (duplicate_of=126) |
| 261 | Futures CVD / Taker Flow | **TIER2** | Futures CVD / Taker Flow — flow metric delivery |
| 262 | Options Open Interest | **TIER2** | Options Open Interest — options metric delivery |
| 263 | Options Volume | **TIER2** | Options Volume — options volume delivery |
| 264 | Options IV / Skew | **TIER2** | Options IV / Skew — options metric delivery |
| 265 | Max Pain / Gamma Context | **TIER2** | Max Pain / Gamma Context — options context metric delivery |
| 266 | Spot Market Intelligence | **TIER2** | Spot Market Intelligence — market data delivery |
| 267 | Order Book / Market Depth | **TIER2** | Order Book / Market Depth — order book delivery |
| 268 | Historical Derivatives Data | **TIER2** | Historical Derivatives Data — historical data delivery |
| 269 | Exchange Comparison | **TIER2** | Exchange Comparison — comparison delivery |
| 270 | Liquidation Cascade Proximity | **TIER1** | Liquidation Cascade Proximity — proximity score influences trading decisions (default-on-doubt) |
| 271 | Leverage Pressure Score | **TIER1** | Leverage Pressure Score — SCORE-IDX surface |
| 272 | API Data Platform | **TIER2** | API Data Platform — data platform delivery (duplicate_of=103) |
| 273 | Multi-Model Liquidation Comparison | **TIER2** | Multi-Model Liquidation Comparison — comparison tool |
| 274 | Derivatives Alerts | **TIER2** | Derivatives Alerts — alert feed delivery |
| 275 | Cross-Domain Decision Intelligence | **TIER1** | Cross-Domain Decision Intelligence — decision output (catalog duplicate link) |
| 276 | Entity Resolution Engine | **TIER2** | Entity Resolution Engine — entity reference/registry |
| 277 | Address Labeling System | **TIER1** | Address Labeling System — on-chain address labeling (FATF R.16) |
| 278 | Entity Profiles | **TIER2** | Entity Profiles — profile catalog delivery |
| 279 | Transaction Search | **TIER1** | Transaction Search — on-chain transaction intelligence (FATF R.16) |
| 280 | Portfolio Holdings | **TIER2** | Portfolio Holdings — holdings delivery |
| 281 | Balance History | **TIER1** | Balance History — wallet balance history tool (FATF R.16) |
| 282 | Entity PnL | **TIER1** | Entity PnL — financial PnL surface |
| 283 | Exchange Usage Intelligence | **TIER2** | Exchange Usage Intelligence — usage metric delivery |
| 284 | Top Counterparties | **TIER2** | Top Counterparties — counterparty list delivery |
| 285 | Visualizer / Network Graph | **TIER2** | Visualizer / Network Graph — visualization delivery |
| 286 | Automated Trace / Path Finding | **TIER1** | Automated Trace / Path Finding — on-chain trace (FATF R.16) |
| 287 | Cross-Chain Trace | **TIER1** | Cross-Chain Trace — on-chain trace (FATF R.16) |
| 288 | Token Top Holders | **TIER1** | Token Top Holders — holder addresses (FATF R.16) |
| 289 | Token Exchange Flows | **TIER1** | Token Exchange Flows — exchange flow transaction intelligence |
| 290 | Token Transaction Explorer | **TIER1** | Token Transaction Explorer — transaction explorer (FATF R.16) |
| 291 | Custom Dashboards | **TIER2** | Custom Dashboards — dashboard delivery |
| 292 | Custom Alerts | **TIER2** | Custom Alerts — alert delivery |
| 293 | Private Labels | **TIER2** | Private Labels — label management delivery |
| 294 | Archive / Historical Portfolio Snapshot | **TIER2** | Archive / Historical Portfolio Snapshot — archive delivery |
| 295 | AI Market Insights | **TIER1** | AI Market Insights — AI surface (NIST AI RMF full path) |
| 296 | Whale Movement Intelligence | **TIER1** | Whale Movement Intelligence — whale/on-chain movement (FATF R.16) |
| 297 | Fraud / Suspicious Activity Intelligence | **TIER1** | Fraud / Suspicious Activity Intelligence — fraud verdict influences user action |
| 298 | API On-Chain Intelligence | **TIER2** | API On-Chain Intelligence — API delivery surface |
| 299 | Cross-Entity Decision Intelligence | **TIER1** | Cross-Entity Decision Intelligence — explicit decision output |
| 300 | Advanced Multi-Asset Charting | **TIER2** | Advanced Multi-Asset Charting — charting delivery |

## Item 3 — RBAS Impact Metrics

| Path | IDs | Phase checks executed | Wall time (ms) |
|---|---:|---:|---:|
| Tier1 (native) | 17 | 153 | 29534 |
| Tier2 (abbreviated) | 29 | 87 | 10171 |
| Tier2→Tier1 escalated | 4 | 48 | 8673 |
| **Total** | 50 | 288 | 48378 |

- **Tier2 efficiency ratio:** 0.64 (abbreviated checks vs full nine-phase baseline of 450)
- **CONCEPTUALLY-UNSOUND:** 0/50 (Tier2 abbreviated path — escalation covers hidden decision logic)
- **RBAS-001 calibration note:** Escalation excludes compliance_footer provenance_score paths (Run 015 calibration). Tier2 abbreviated path did not yield CONCEPTUALLY-UNSOUND misses.

## Item 4 — SPLIT-BRAIN (mandatory all 50)

- **DEDICATED_ONLY:** 50/50

## Item 5 — Diagnostic Classification Summary

- **NOT_COMPLETE:** 44/50
- **PERFORMANCE-UNVERIFIABLE:** 6/50

## Item 6 — Closure Gate (Batch06 NOT closed in Run 015)

| Criterion | Status |
|---|---|
| CONCEPTUALLY-UNSOUND = 0 | **MET ✅** (0) |
| RTM honest (pending closure run) | **NOT YET** — diagnostic only |
| Batch07 opening | **BLOCKED** until Batch06 closure |

## Cross-Spine Run 015 Actions

- WF-027: **zero overlap** with Batch06 range — no legacy ID removal required
- Catalog duplicates retained with batch06 dedicated handlers: 251/275, 255→205, 256→86, 257→235, 260→126, 272→103
- `batch06_production` + `batch06_dedicated` + runtime `BATCH06_IDS` registered

Full audit: `BATCH06_INDEPENDENT_RBAS_AUDIT_REPORT.md`
