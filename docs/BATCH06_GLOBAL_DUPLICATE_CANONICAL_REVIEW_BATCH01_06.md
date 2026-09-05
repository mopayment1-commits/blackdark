# Batch06 Global Duplicate / Canonical Review (Batches 01–06)

**Generated:** 2026-09-05T00:06:41.759652+00:00 · **Commit:** `25017eef`

## Summary

| Metric | Value |
|--------|------:|
| Total IDs | 50 |
| REUSED-LINK | 11 |
| Strangler | 39 |
| Surface collision IDs | 5 |
| New hidden duplicates | 0 |

## Decision breakdown

- **DISTINCT**: 39
- **REUSED-LINK**: 11

## REUSED-LINK cross-batch canonical map

| ID | Canonical | Spine | Binding |
|----|-----------|-------|---------|
| 251 | #69 | batch02 | `cap646/batch02_production.py::cap_069` |
| 255 | #205 | batch05 | `cap646/batch05_strangler_spine.py::build_open_interest_205` |
| 256 | #86 | batch02 | `cap646/batch02_production.py::cap_086` |
| 257 | #235 | batch05 | `cap646/batch05_strangler_spine.py::build_long_short_ratio_intelligence_235` |
| 259 | #231 | batch05 | `cap646/batch05_strangler_spine.py::build_futures_basis_term_structure_231` |
| 260 | #126 | batch03 | `cap646/batch03_dedicated.py::_cap126` |
| 261 | #234 | batch05 | `cap646/batch05_strangler_spine.py::build_cvd_intelligence_234` |
| 272 | #247 | batch05 | `cap646/batch05_strangler_spine.py::build_public_rest_api_247` |
| 275 | #69 | batch02 | `cap646/batch02_production.py::cap_069` |
| 291 | #210 | batch05 | `cap646/batch05_strangler_spine.py::build_custom_dashboards_layouts_210` |
| 292 | #213 | batch05 | `cap646/batch05_strangler_spine.py::build_anomaly_detection_alerts_213` |

Full JSON: `docs/BATCH06_GLOBAL_DUPLICATE_CANONICAL_REVIEW_BATCH01_06.json`
