# Analyst Notes & Source Provenance — #206, #208

## #206 — Analyst Notes Feed (Sprint 2 lightweight)

**NOT a consensus engine** — Wave 3 consensus deferred.

| Rule | Implementation |
|------|----------------|
| Attribution | `Analyst: @name \| Firm: X \| Date: YYYY-MM-DD` |
| Not a prediction | `Analyst View: Bullish/Neutral/Bearish \| Confidence: X%` |
| Disclaimer | Non-hideable: "Analyst views are opinions, not facts." |
| Divergence | `5 analysts: 3 Bullish \| 1 Neutral \| 1 Bearish` — no average |

### APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/analyst-notes` | List notes (filter by asset/firm/view) |
| `GET /api/platform/analyst-notes/summary/{asset}` | Divergence counts |
| `GET /api/platform/analyst-notes/{id}` | Note detail |
| `GET /api/platform/analyst-notes/status` | Module status |

---

## #208 — Source Registry & Provenance Layer (Sprint 0, merged #118)

| Policy | Implementation |
|--------|----------------|
| No undocumented source | Registry from `data_sources_registry` |
| Secrets never in logs | Redaction + vault references only |
| Rights/license verified | Per-source `license_status` |
| Raw vs normalized | `raw_checksum` + `normalization_checksum` |
| Deterministic normalization | Same input → same checksum |
| Reconciliation | `Source A: X \| Source B: Y \| Variance: Z%` |
| Audit evidence | `data/provenance/audit_trail.jsonl` |
| Provider failure tests | 24h degradation probe via coverage map |

### APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/provenance/status` | Layer policies |
| `GET /api/platform/provenance/registry` | Full source map |
| `GET /api/platform/provenance/lineage/{metric}` | Metric lineage chain |
| `POST /api/platform/provenance/reconcile` | Source reconciliation |
| `POST /api/platform/provenance/provider-test` | Degradation test |
| `GET /api/v1/platform/provenance/status` | Unified API alias |
