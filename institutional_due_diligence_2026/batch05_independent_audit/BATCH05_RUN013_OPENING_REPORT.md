# Batch 05 Run 013 — RBAS-001 Opening Diagnostic Report (IDs 201–250)

**Generated:** 2026-09-11T09:04:53.196099+00:00  
**Run:** Master Contract 013  
**Policies:** RBAS-001 | RTM-IND-001 | SCORE-IDX-001 | CROSS-SPINE-001 | WF-027  

## Item 1 — WF-027 Preflight (mandatory first)

- **WF-027 dormant legacy set (10 IDs):** `[175, 214, 245, 584, 629, 630, 631, 642, 644, 646]`
- **Batch05 official range:** 201-250
- **Intersection (overlap):** `[214, 245]` — **2/10** IDs
- **Non-overlap IDs (8/10 outside 201–250):** confirmed — 175, 584, 629, 630, 631, 642, 644, 646 lie outside Batch05 scope
- **Preflight evidence:** WF-027 set=[175, 214, 245, 584, 629, 630, 631, 642, 644, 646]; Batch05 range 201-250; intersection=[214, 245] (2/10 WF-027 IDs in scope)
- **Run 013 cross-spine action:** IDs **214** and **245** removed from `LEGACY_BATCH01_EXTENSION_IDS` and batch01 routing maps; dedicated `batch05_dedicated` handlers registered

## Item 2 — Pre-Audit Tier Classification (50/50)

- **Tier1:** 14/50 (full nine-phase)
- **Tier2:** 36/50 (abbreviated path)

See `RBAS001_TIER_CLASSIFICATION_BATCH05.json` for per-ID reasons.

### Tier Table Summary

| ID | Capability | Tier | Reason |
|---:|---|---|---|
| 201 | Network Growth Intelligence | **TIER2** | Network growth intelligence — on-chain metric delivery (no user verdict score) |
| 202 | Supply Distribution Intelligence | **TIER2** | Supply distribution intelligence — distribution metric delivery |
| 203 | DEX Trading Intelligence | **TIER2** | DEX trading intelligence — market data delivery |
| 204 | DeFi Protocol Activity Intelligence | **TIER2** | DeFi protocol activity intelligence — activity metric delivery |
| 205 | Open Interest Intelligence | **TIER2** | Open Interest Intelligence — derivatives metric delivery |
| 206 | Funding Rate Intelligence | **TIER2** | Funding Rate Intelligence — metric delivery (duplicate_of=86) |
| 207 | Price / Volume / Market Metrics | **TIER2** | Price / Volume / Market Metrics — market metric delivery |
| 208 | Metric Correlation Workbench | **TIER2** | Metric Correlation Workbench — analysis workbench (no score output) |
| 209 | Custom Chart Builder | **TIER2** | Custom Chart Builder — chart builder delivery |
| 210 | Custom Dashboards / Layouts | **TIER2** | Custom Dashboards / Layouts — dashboard delivery |
| 211 | Screener | **TIER2** | Screener — screening tool without scored verdict |
| 212 | Smart Alerts | **TIER2** | Smart Alerts — alert delivery (duplicate_of=17) |
| 213 | Anomaly Detection Alerts | **TIER2** | Anomaly Detection Alerts — alert feed delivery |
| 214 | Watchlists | **TIER1** | WF-027 dormant legacy ID — Watchlists (T11); mandatory full audit |
| 215 | Community Explorer | **TIER2** | Community Explorer — catalog/explorer delivery |
| 216 | Research & Market Insights | **TIER2** | Research & Market Insights — research delivery |
| 217 | SanAPI-Style Data Access | **TIER2** | SanAPI-Style Data Access — data access delivery |
| 218 | Google Sheets Integration | **TIER2** | Google Sheets Integration — integration delivery |
| 219 | Metric Availability Registry | **TIER2** | Metric Availability Registry — registry/catalog |
| 220 | Data Stabilization & Mutability Metadata | **TIER2** | Data Stabilization & Mutability Metadata — metadata delivery |
| 221 | Data Quality & Provenance Layer | **TIER2** | Data Quality & Provenance Layer — provenance delivery (duplicate_of=63) |
| 222 | Metric Methodology Registry | **TIER2** | Metric Methodology Registry — methodology registry |
| 223 | Social-to-On-Chain Confirmation Engine | **TIER1** | Social-to-On-Chain Confirmation Engine — confirmation/decision output |
| 224 | Narrative Actionability Score | **TIER1** | Narrative Actionability Score — SCORE-IDX surface |
| 225 | Development-to-Market Divergence Detector | **TIER1** | Development-to-Market Divergence Detector — divergence signal influences decisions |
| 226 | Cross-Domain Decision Intelligence Layer | **TIER1** | Cross-Domain Decision Intelligence Layer — explicit decision output |
| 227 | Unified Trading Intelligence Workspace | **TIER1** | Unified Trading Intelligence Workspace — trading decision workspace |
| 228 | Funding Rate Intelligence | **TIER2** | Funding Rate Intelligence — metric delivery (duplicate_of=86) |
| 229 | Cross-Exchange Funding Arbitrage Scanner | **TIER1** | Cross-Exchange Funding Arbitrage Scanner — arbitrage/trading decision surface |
| 230 | Spot-Perp Arbitrage Scanner | **TIER1** | Spot-Perp Arbitrage Scanner — arbitrage/trading decision surface |
| 231 | Futures Basis & Term Structure | **TIER2** | Futures Basis & Term Structure — term structure metric delivery |
| 232 | Open Interest Intelligence | **TIER2** | Open Interest Intelligence — metric delivery (duplicate_of=205) |
| 233 | Liquidation Intelligence | **TIER2** | Liquidation Intelligence — metric delivery (duplicate_of=88) |
| 234 | CVD Intelligence | **TIER2** | CVD Intelligence — volume delta metric delivery |
| 235 | Long/Short Ratio Intelligence | **TIER2** | Long/Short Ratio Intelligence — ratio metric delivery |
| 236 | DEX Screener | **TIER2** | DEX Screener — screener delivery |
| 237 | Token Risk Scoring | **TIER1** | Token Risk Scoring — SCORE-IDX surface |
| 238 | Pump & Dump Detection | **TIER1** | Pump & Dump Detection — detection verdict influences user action |
| 239 | Narrative Tracking | **TIER2** | Narrative Tracking — narrative catalog tracking |
| 240 | Sector Rotation Intelligence | **TIER1** | Sector Rotation Intelligence — portfolio allocation decision-adjacent |
| 241 | Sentiment Intelligence | **TIER1** | Sentiment Intelligence — sentiment index (duplicate_of=129; SCORE-IDX pattern) |
| 242 | Price Prediction / Multi-Signal Forecast | **TIER1** | Price Prediction / Multi-Signal Forecast — AI prediction (NIST AI RMF full path) |
| 243 | Correlation Matrix | **TIER2** | Correlation Matrix — correlation data tool |
| 244 | New Listings Intelligence | **TIER2** | New Listings Intelligence — listings feed delivery |
| 245 | Market Health & Freshness | **TIER1** | WF-027 dormant legacy ID — Market Health & Freshness (T13); mandatory full audit |
| 246 | Coverage Metadata Registry | **TIER2** | Coverage Metadata Registry — coverage registry |
| 247 | Public REST API | **TIER2** | Public REST API — API delivery surface |
| 248 | MCP Server for AI Agents | **TIER2** | MCP Server for AI Agents — platform delivery |
| 249 | CLI Access | **TIER2** | CLI Access — CLI delivery |
| 250 | OpenAPI / SDK Generation | **TIER2** | OpenAPI / SDK Generation — SDK generation delivery |

## Item 3 — RBAS Impact Metrics

| Path | IDs | Phase checks executed | Wall time (ms) |
|---|---:|---:|---:|
| Tier1 (native) | 14 | 126 | 13071 |
| Tier2 (abbreviated) | 28 | 84 | 9610 |
| Tier2→Tier1 escalated | 8 | 96 | 27267 |
| **Total** | 50 | 306 | 49948 |

- **Tier2 efficiency ratio:** 0.68 (abbreviated checks vs full nine-phase baseline of 450)
- **CONCEPTUALLY-UNSOUND:** 0/50 (Tier2 abbreviated path — escalation covers hidden decision logic)
- **RBAS-001 calibration note:** Escalation excludes compliance_footer provenance_score paths (Run 013 calibration). Tier2 abbreviated path did not yield CONCEPTUALLY-UNSOUND misses.

## Item 4 — SPLIT-BRAIN (mandatory all 50)

- **DEDICATED_ONLY:** 50/50

## Item 5 — Diagnostic Classification Summary

- **NOT_COMPLETE:** 39/50
- **PERFORMANCE-UNVERIFIABLE:** 11/50

## Item 6 — Closure Gate (Batch05 NOT closed in Run 013)

| Criterion | Status |
|---|---|
| CONCEPTUALLY-UNSOUND = 0 | **MET ✅** (0) |
| RTM honest (pending closure run) | **NOT YET** — diagnostic only |
| Batch06 opening | **BLOCKED** until Batch05 closure |

## Cross-Spine Run 013 Actions

- ID **214** (Watchlists) + ID **245** (Market Health & Freshness) removed from batch01 legacy spine
- Catalog duplicates retained with batch05 dedicated handlers: 206→86, 212→17, 221→63, 222→64, 226→69, 228→86, 232→205, 233→88, 241→129
- `batch05_production` + `batch05_dedicated` + runtime `BATCH05_IDS` registered

Full audit: `BATCH05_INDEPENDENT_RBAS_AUDIT_REPORT.md`
