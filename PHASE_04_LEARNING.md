# PHASE 04 — Learning Compounding

**Status:** ✅ Complete

## Deliverables
- `learning_predictions`, `learning_outcomes`, `counterfactual_log` tables
- `GET /api/oracle/accuracy` — historical track record (oracle + learning registry)
- `GET /api/opportunities/missed` — from `public_miss_feed` + counterfactuals
- `POST /api/learning/counterfactuals` — what-if log

## Verify
```bash
curl -sS "$BASE/api/compounding/_verify/phase/4"
curl -sS "$BASE/api/oracle/accuracy"
curl -sS "$BASE/api/opportunities/missed"
```
