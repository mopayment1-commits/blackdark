# Run 021 — Real Logic Remediation Plan (1–826)

**Generated:** 2026-09-11  
**Standard:** Path A mandatory — `catalog_binding_executor` (SSOT `backend_registry`) or goal-specific custom handler. **No `invoke_underlying` keyword routing.**

## Technical scope (not calendar estimates)

| Phase | Scope | IDs | Handler pattern | Complexity |
|---|---|---|---|---|
| **A — Confirm** | Batch01–03 Phase 1 gate | 150 | Already real (137 dedicated + 13 production-routed) | **Done** — see `RUN021_PHASE1_CONFIRM_01_03.json` |
| **B — Batch13** | Real logic + re-close | 601–650 (50) | 46× `catalog_binding_executor` + 4× custom (647–650) | **Medium** — automated regen + live verify all 50 |
| **C — Batch04–12** | Replace generic-delegate debt | 151–600 (450) | Regenerate via `regenerate_real_logic_dedicated.py` per batch | **High volume, low per-ID cost** — 9 batch runs + 50 live samples each |
| **D — Batch14–17** | Open/close from scratch | 651–826 (176) | Spine factory + catalog_binding from first commit | **Medium** — no legacy invoke_underlying debt if factory updated |

**Total generic-delegate IDs before fix:** 494 (batch04–13)  
**Automation:** `scripts/regenerate_real_logic_dedicated.py` + `cap646/catalog_binding_executor.py`

## Why `catalog_binding_executor` is Path A (not fake)

`invoke_underlying` keyword-routes to **wrong generic domain handler** (e.g. ID 307 → alerts inbox, not `smart_alerts_307`).

`catalog_binding_executor` calls **`backend_registry.resolve_binding(id)`** → exact `module.entrypoint` for that capability (e.g. 601 → `onchain_tracker.build_onchain_context_safe`, 604 → `bd_platform.token_unlocks.unlock_calendar`).

Each payload includes:
```json
"methodology": {
  "framework": "Path A — catalog_binding_executor (SSOT backend_registry)",
  "implementation": "<module>.<entrypoint>",
  "methodology_status": "DOCUMENTED"
}
```

## Execution order (user-approved)

1. ✅ **Batch01–03 confirm** — 150/150 CLEAN (0 generic-delegate)
2. **Batch13** — regenerate 601–646 + re-audit + re-close under real-logic gate
3. **Batch04→12** — one batch per PR slice (151–200 first), live verify 10-ID random sample per batch
4. **Batch14→17** — orchestrator resume with updated spine factory

## Acceptance per capability

- [ ] Dedicated handler uses `execute_catalog_binding` or custom Path A (584/647 style)
- [ ] Phase 1 generic-delegate: PASS
- [ ] Live `execute_capability(id)` → `success=true` + documented methodology
- [ ] No `invoke_underlying` in handler source

## Batch13 status

Previous closure (NOT_COMPLETE=50 with generic-delegate documented) **superseded** — handlers regenerated 2026-09-11 with Path A. Re-audit required before final re-close.
