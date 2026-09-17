# B4 Temporal Independent Verification Report (Re-IV)

**Prior IV SHA:** `4a691f4d` — `NOT_COMPLETE` (UNTRUSTED_DECISION_TIME_ASSERTION)  
**Remediation SHA:** `7a930bf1`  
**Re-IV at:** 2026-09-17T14:26:00+00:00

---

## SECTION A — Remediation (builder)

| Field | Value |
|-------|-------|
| Status | `PENDING_VERIFICATION` |
| Defect | `UNTRUSTED_DECISION_TIME_ASSERTION` |
| Fix | `build_decision_timing_context`: when `require_authoritative_decision_time=True`, accept `decision_time` only from `governed_payload` |
| Files touched | `launch57/decision_timing_common.py`, `tests/launch57/test_temporal_batch4.py` |
| Builder claim | `PASS_ENGINEERING_NOT_CLAIMED` |

Evidence: `governance/launch57/B4_TEMPORAL_REMEDIATION_EVIDENCE.json`

---

## SECTION B — Independent re-check verdict

### Tests re-run

```bash
python3 -m pytest tests/launch57/test_temporal_batch4.py tests/launch57/test_trust_batch1.py -v
```

20 passed, 0 failed (includes new `test_certificate_rejects_caller_only_decision_time`).

### Summary table

| Item | Verdict |
|------|---------|
| #2 | PASS_ENGINEERING |
| #3 | PASS_ENGINEERING |
| SPEC §13-5 | PASS_ENGINEERING |
| B4_INDEPENDENT_VERDICT | PASS_ENGINEERING |

| ID / Requirement | Verdict | Evidence |
|------------------|---------|----------|
| #2 temporal fields | PASS_ENGINEERING | `test_oracle_includes_canonical_decision_and_issued_times`; runtime probe success |
| #3 cert temporal + hash | PASS_ENGINEERING | Caller-only `decision_time` fails closed; governed path emits deterministic hash |
| Evidence trust gate #2/#3 | PASS_ENGINEERING | `test_oracle_caller_evidence_escalation_blocked`; evidence snapshot on cert |
| Isolation B4 path | PASS_ENGINEERING | No `cap646` imports on B4 modules |
| SPEC §13-1 issued time | PASS_ENGINEERING | `issued_at` + `temporal.decision_time` on emit |
| SPEC §13-2 decision-time evidence | PASS_ENGINEERING | `evidence_class_common.assess_user_evidence_class` |
| SPEC §13-3 review/recheck | PASS_ENGINEERING | `_validate_not_before` |
| SPEC §13-4 invalidation | PASS_ENGINEERING | Append-only invalidation fields |
| SPEC §13-5 certificate timestamp/hash | PASS_ENGINEERING | Deterministic hash; untrusted caller `decision_time` rejected |
| SPEC §13-6 TZ immutability | PASS_ENGINEERING | `test_tz_display_does_not_mutate_canonical_decision_time` |

### Adversarial runtime (re-IV)

| Probe | Input | Observed | Pass |
|-------|-------|----------|------|
| Caller-only decision_time (#3) | `decision_time=2020-01-01T00:00:00.000Z`, no `governed_payload` | `success=false`, `error=decision_time_required` | ✓ |
| Governed decision_time (#3) | `governed_payload.decision_time=2026-09-17T12:00:00.000Z` | `success=true`, hash `e04d2cb1…` | ✓ |
| Missing decision_time | `{}` | `decision_time_required` | ✓ |
| Hash determinism | Identical governed inputs ×2 | Identical `certificate_hash` | ✓ |

### Prior blocker — closed

**UNTRUSTED_DECISION_TIME_ASSERTION** — remediated at `7a930bf1`; re-IV confirms caller-only backdated `decision_time` no longer produces authoritative certificate.

### Out of scope (documented)

`launch57/trust_batch2.py` still uses `decision_certificate.build_decision_certificate` for Launch #44 — not evaluated for B4 PASS.

### Flags

- `B4_INDEPENDENT_VERDICT = PASS_ENGINEERING`
- `PASS_LIVE_NOT_CLAIMED = true`
- `LAUNCH57_TEMPORAL_CONSISTENCY_PASS_ENGINEERING = false` (global; B4 batch only)
- `B5_NOT_STARTED = true`
