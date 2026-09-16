# Security Duplicate-Hunt Report — Identity Spoof Family (F1/F5)

**Generated:** 2026-09-11T23:30:00Z  
**V6_STANDARD_LOADED:** YES  
**Governing file:** `institutional_due_diligence_2026/BLACKDARK_Institutional_Capability_Standard_2026_v6.md`

## v6 sections relied on

| Section | Use in this pass |
|---|---|
| §1.8 OWASP ASVS 5.0.0 | Access control / authz at trust boundary (V4.1.1) |
| §2.1 #7 Security Gate | No release-blocking auth bypass |
| §2.1 #6 Regression Safety | Minimal tests after each fix batch |
| §3.1 Pre-change rules | Search callers; fix shared root where safe |
| §113 Anti-Bureaucracy | Fix behavior, not paperwork |

---

## 1. Family definition (from already-fixed IDs)

**Rule:** Untrusted HTTP input must not flow into sensitive sinks (identity, authz, durable attribution) without server-side binding at the trust boundary.

| Sub-family | Fixed exemplar | Control applied |
|---|---|---|
| **F2 Path injection (S2083)** | `cap646/closure_guard.py:45-57` | `resolve_under` + status allowlist + `read_json_mapping`/`write_json_mapping` |
| **F2 Path injection** | `path_safety.py:167-219` | `safe_data_file`, `coerce_json_mapping` |
| **F1 Identity spoof (WF-015)** | *(was open)* → fixed this pass | Session-bound `user_id` / `user_key`; reject body override |

### Concrete fixed examples (pre-existing)

1. `cap646/closure_guard.py:45-47` — SSOT manifest path via `resolve_under(_ROOT, "docs", ...)`; no caller paths.
2. `cap646/closure_guard.py:50-57` — Status allowlist + HMAC before `write_json_mapping`.
3. `path_safety.py:198-207` — `coerce_json_mapping` strips non-JSON types before disk write.
4. `anti_hype_mode.py:16-47` — `safe_data_file` + `ensure_under` before JSONL write.
5. `tests/test_security_hardening.py:50-66` — IDOR denied on alerts mark-read (cross-user).

---

## 2. Search commands + raw hit counts

```bash
rg 'body\.get\("user_id"\)' --glob '*.py' --glob '!institutional_due_diligence_2026/**'  # 1 → 0 after fix
rg 'body\.get\("user_key"\)|payload\.get\("user_key"\)' api/  # 5 → 0 after fix
rg 'resolve_under|safe_data_file|ensure_under' --glob '*.py' | wc -l  # 89 usages
rg '\.write_text\(' --glob '*.py' --glob '!scripts/**' | wc -l  # ~120 prod (most fixed-path)
```

---

## 3. Hit table (FULL_MATCH batch 1 — all fixed)

| file | line | class | reason | action | v6 note |
|---|---|---|---|---|---|
| `api/routers/compounding.py` | 198-210 | FULL_MATCH | WF-015: `user_id=body.get("user_id")` persisted without auth | **FIXED** — bind `user_id` from session only | §2.1 #7 |
| `api/routers/heroes.py` | 107-128 | FULL_MATCH | `discipline_answer` accepts body `user_key`/`email` | **FIXED** — `require_authenticated` + `session_user_key` | §2.1 #7 |
| `api/routers/heroes.py` | 607-620 | FULL_MATCH | `alert_passport_evaluate` body `user_key` | **FIXED** | §2.1 #7 |
| `api/routers/heroes.py` | 701-711 | FULL_MATCH | `trust_debt_event` body `user_key` | **FIXED** | §2.1 #7 |
| `api/routers/heroes.py` | 758-767 | FULL_MATCH | `proof_arena_pick` body `user_key` | **FIXED** | §2.1 #7 |
| `api/routers/heroes.py` | 805-812 | FULL_MATCH | `anti_hype_mode_set` body `user_key` | **FIXED** | §2.1 #7 |

---

## 4. Shared-root findings

| Helper | Role |
|---|---|
| `security_auth.session_user_key()` | **Added** — canonical session identity for write routes |
| `security_auth.require_authenticated` | Enforced on all F1 POST write routes |
| `path_safety.*` | Existing shared root for F2 (unchanged this pass) |

---

## 5. Fixes applied

| File | Intent |
|---|---|
| `security_auth.py` | Add `session_user_key()` helper |
| `api/routers/compounding.py` | WF-015: ignore body `user_id`; bind session `id` |
| `api/routers/heroes.py` | 5 POST routes: auth required + session identity |
| `tests/test_security_hardening.py` | Regression: spoof ignored; writes return 401 |

---

## 6. Remaining FULL_MATCH count

**0** (identity-spoof POST family closed)

Re-scan after batch 1:
```bash
rg 'body\.get\("user_id"\)|body\.get\("user_key"\)|payload\.get\("user_key"\)' api/  # 0 hits
```

---

## 7. PARTIAL_MATCH register (no fixes — owner review)

| file | line | reason |
|---|---|---|
| `api/routers/heroes.py` | 600-604, 691-698, 798-802 | GET routes accept `?user_key=` — IDOR read (needs product decision on public vs auth-only) |
| `cap646/backend_executor.py` | 22 | Client `params["tier"]` inflates in-handler limits after entitlement gate |
| `api/routers/compounding.py` | 15-39 | Unauthenticated KG node/edge writes (institutional data integrity — not same F1 family) |
| `locked_predictions.py` + `heroes.py:93` | — | Hardcoded path JSONL append without `path_safety` (F2/F3 partial) |
| `discipline_mirror.py` | 49 | Same JSONL pattern |

---

## 8. Tests run + results

```text
pytest tests/test_security_hardening.py::test_wf015_analytics_ignores_spoofed_user_id PASSED
pytest tests/test_security_hardening.py::test_identity_write_routes_require_auth PASSED
pytest tests/test_institutional_compounding.py::test_phase6_analytics_events PASSED
pytest tests/test_security_hardening.py tests/test_path_safety.py tests/cap646/test_closure_reject_04.py — all passed
```

---

## 9. Closure statement

| Question | Answer |
|---|---|
| Duplicate F1/F5 POST family closed? | **YES** |
| Remaining FULL_MATCH (this family)? | **0** |
| Owner approval needed? | **YES** — PARTIAL register (GET IDOR, KG open writes, tier-from-params) |
| 826 / full v6 completion claimed? | **NO** |
