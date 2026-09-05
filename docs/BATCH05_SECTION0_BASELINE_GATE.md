# Batch05 Section 0 — Baseline Gate + Prior Work Census

**Generated:** 2026-09-04T10:09:14.558407+00:00  
**Commit:** `de59160126689c519f65154d884de69d79bd76a4`  
**Branch:** `cursor/batch05-201-250-e85e`  
**Scope:** Official Batch05 IDs **201–250** (50 capabilities)

---

## 1. Sequential baseline gate (Batch01–04)

| Batch | ID range | Engineering closure | PRODUCTION-ALIGNED | Notes |
|-------|----------|---------------------|-------------------:|-------|
| Batch01 | 1–50 | LOCAL_GOVERNANCE_COMPLETE | **50/50** | `docs/BATCH01_826_COMPLETION_REPORT.md` |
| Batch02 | 51–100 | LOCAL_GOVERNANCE_COMPLETE | **50/50** | `docs/BATCH02_HONEST_CLOSURE_AUDIT.md` |
| Batch03 | 101–150 | LOCAL_GOVERNANCE_COMPLETE | **44 PA + 4 REUSED-LINK + 2 OVERLAP-PARTIAL** | `docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md` |
| Batch04 | 151–200 | BUILD_PHASE_LIFTED (not full 50/50 PA) | **31/50** | {'PRODUCTION-ALIGNED': 31, 'NOT_COMPLETE': 19} — accepted per owner gate |

**progress_826 canonical:** `179/826` (`docs/PROGRESS_826_CANONICAL.json`)

### Non-regression at gate open

```bash
.venv/bin/python -m pytest tests/cap646/test_batch01_dedicated.py ... test_batch04_strangler_spine.py
```

**Result @ `de59160126689c519f65154d884de69d79bd76a4`:** `749 passed, 1 deselected` (log: `/opt/cursor/artifacts/batch05_gate_nonregression.log`)

**Gate decision:** Batch05 **OPEN** — prior batches closed for governance purposes; Batch04 partial PA acknowledged.

---

## 2. Prior unofficial work on 201–250

| Finding | Count | Disposition |
|---------|------:|-------------|
| Official `cap646/batch05_*` spine | **0** | Build net-new |
| Official `tests/cap646/test_batch05_*` | **0** | Build net-new |
| Hero Batch03 evidence (lines 1–50) | **50** | REUSE-AUDIT-INPUT only |
| `bd_platform` hero functions `*_201..250` | **50** | Brownfield input — SPLIT-BRAIN until spine wired |
| Batch01 overlap (#214 dedicated, #245 production) | **2** | RECLASSIFY-OVERLAP before PA |
| Misnumbered `run_batch05_deep_closure.py` (401–500) | 1 | **IGNORE** — not official Batch05 |

Full census: `docs/BATCH05_PRIOR_WORK_CENSUS_201_250.json`

---

## 3. 12207 lifecycle classification (all 50 IDs)

| Class | Count |
|-------|------:|
| Brownfield | 48 |
| Brownfield-OVERLAP-BATCH01 | 2 |

**No `_base/_metric` template stubs detected** in 201–250 hero functions (mandate §27).

---

## 4. INVEST — per-ID table (mandate §5)

Full machine-readable rows (each I/N/V/E/S/T with individual evidence): `docs/BATCH05_CLASSIFICATION_INVEST_201_250.json`

| ID | Capability | 12207 | I | N | V | E | S | T | Prior disposition |
|---:|------------|-------|:-:|:-:|:-:|:-:|:-:|:-:|-------------------|
| 201 | Network Growth Intelligence | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 202 | Supply Distribution Intelligence | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 203 | DEX Trading Intelligence | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 204 | DeFi Protocol Activity Intelligence | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 205 | Open Interest Intelligence | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 206 | Funding Rate Intelligence | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 207 | Price / Volume / Market Metrics | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 208 | Metric Correlation Workbench | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 209 | Custom Chart Builder | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 210 | Custom Dashboards / Layouts | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 211 | Screener | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 212 | Smart Alerts | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 213 | Anomaly Detection Alerts | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 214 | Watchlists | Brownfield-O | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | RECLASSIFY-OVERLAP-BATCH01 |
| 215 | Community Explorer | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 216 | Research & Market Insights | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 217 | SanAPI-Style Data Access | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 218 | Google Sheets Integration | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 219 | Metric Availability Registry | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 220 | Data Stabilization & Mutability Metadata | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 221 | Data Quality & Provenance Layer | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 222 | Metric Methodology Registry | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 223 | Social-to-On-Chain Confirmation Engine | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 224 | Narrative Actionability Score | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 225 | Development-to-Market Divergence Detecto | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 226 | Cross-Domain Decision Intelligence Layer | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 227 | Unified Trading Intelligence Workspace | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 228 | Funding Rate Intelligence | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 229 | Cross-Exchange Funding Arbitrage Scanner | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 230 | Spot-Perp Arbitrage Scanner | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 231 | Futures Basis & Term Structure | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 232 | Open Interest Intelligence | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 233 | Liquidation Intelligence | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 234 | CVD Intelligence | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 235 | Long/Short Ratio Intelligence | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 236 | DEX Screener | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 237 | Token Risk Scoring | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 238 | Pump & Dump Detection | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 239 | Narrative Tracking | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 240 | Sector Rotation Intelligence | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 241 | Sentiment Intelligence | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 242 | Price Prediction / Multi-Signal Forecast | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 243 | Correlation Matrix | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 244 | New Listings Intelligence | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 245 | Market Health & Freshness | Brownfield-O | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | RECLASSIFY-OVERLAP-BATCH01 |
| 246 | Coverage Metadata Registry | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 247 | Public REST API | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 248 | MCP Server for AI Agents | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 249 | CLI Access | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |
| 250 | OpenAPI / SDK Generation | Brownfield | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | REUSE-AUDIT-INPUT-NOT-AUTO-PA |

---

## 5. Next step (not started in this deliverable)

- Create `docs/BATCH05_ACCEPTANCE_201_250.json` (domain_rules before probe)
- MECE dedup scan (1225 + 10000 + hero + 200 pairs)
- Build `cap646/batch05_dedicated.py` strangler spine

**Status:** Classification-only gate — **no implementation claims**.

