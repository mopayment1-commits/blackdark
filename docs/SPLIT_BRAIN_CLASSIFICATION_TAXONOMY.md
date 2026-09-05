# Split-Brain Classification Taxonomy (CLOSURE-MANDATE-FINAL item 6)

| Status | Definition | Gate impact | Example IDs in 1-100 |
|--------|------------|-------------|----------------------|
| `SPLIT_BRAIN_GENERIC_HANDLER` | Hero audit found generic handler routing; **official spine now dispatches to dedicated `batch0N_production` backend** with live goal-specific surface | **Acceptable** — counted in 104 if PRODUCTION-ALIGNED | #25, #46 |
| `SPLIT_BRAIN_REUSED` | Duplicate goal served via canonical spine; outputs match catalog goal | **Acceptable** | #3, #4, #55 |
| `SPLIT_BRAIN_OTHER` | Historical parallel module documented; spine + parallel module may differ; requires dual-path contract | **Review** | #1, #10, #629 |
| `SPLIT-BRAIN-UNVERIFIED` | Inventory `hero_classification=SPLIT-BRAIN-UNVERIFIED` **without** batch01/02 RTM+HTTP proof | **Excluded from 104 numerator** | #584 (excluded) |

**826 RTM field:** always `PRODUCTION-ALIGNED` or `NOT_COMPLETE` via `cap646/rtm_classification.py` — never `VERIFIED_COMPLETE`.

**cap978 gate field:** `INSTITUTIONAL_GATE_PASS` via `cap978/gate_verdict.py` — never mapped to RTM.
