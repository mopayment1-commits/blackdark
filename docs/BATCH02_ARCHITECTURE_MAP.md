# Batch 02 Architecture — Execution Map (CLOSURE-REJECT-04 item 26)

| Layer | File | Executes? | Scope | Notes |
|-------|------|-----------|-------|-------|
| Runtime router | `cap646/runtime.py` | Routes | 51–100 | Dispatches `BATCH02_IDS` to `handle_batch02_capability` |
| Handler wrapper | `cap646/handlers/batch02.py` | Delegates | 51–100 | Calls `route_batch_capability(batch02_production.execute)` |
| Batch spine helper | `cap646/batch_spine.py` | **Yes** | 1–100 | `execute_and_enrich_batch()` — Template Method (MANDATE-FINAL item 2) |
| Production spine | `cap646/batch02_production.py` | **Yes** | 51–100 | `execute()` — overlap IDs 55,56,59,60 → batch01; others → dedicated |
| Dedicated impl | `cap646/batch02_dedicated.py` | **Yes** | 51–54, 57–58, 61–100 | `_cap051`…`_cap100` async handlers |
| Batch01 overlap | `cap646/batch01_production.py` | **Yes** | 55,56,59,60 | OVERLAP_BATCH01 — no batch02 handler |

**R0801 source (pre-r2):** `batch01.py` / `batch02.py` / `batch03.py` identical bodies. **Post-r2:** shared `_batch_route.py`; pylint targets handler package if any residual similarity remains.
