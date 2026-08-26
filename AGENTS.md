# BLACKDARK — Agent Implementation Standards (MANDATORY)

**Status:** ACTIVE — every agent turn MUST follow this file before designing or shipping capabilities.  
**Authority:** User directive + `docs/governing/INSTITUTIONAL_GOVERNING_REFERENCE.md` + `MASTER_PLAN.md`

---

## 1. Binary verdict

- Only `VERIFIED COMPLETE` or `NOT READY` — never "mostly ready".
- Label gaps: `NOT VERIFIED`, `EXTERNAL EVIDENCE`, `HUMAN_OPS` explicitly.
- Never claim acquisition-ready without Evidence Room proof.

## 2. Zero-to-Finish (every capability)

Each feature is complete only when ALL exist:

| Layer | Requirement |
|-------|-------------|
| Logic | `bd_platform/<module>.py` — deterministic, versioned formula |
| Data | Real APIs preferred; seed labeled `BACKTESTED`; missing → `غير متوفر` never `0` |
| API | `/api/platform/...` routes with status + panel + reconciliation tests |
| UI | User can operate from browser — `/intelligence-ledger` hub or dedicated page |
| UX | Loading + Empty + Error states; dark theme; responsive |
| Tests | Unit + integration API; hub E2E where UI exists |
| Docs | `docs/features/<NAME>.md` |
| Evidence | `evidence_class` on every output; compliance footer on financial/AI |

## 3. Forbidden (programmatic enforcement)

- Placeholder buttons, empty pages, "API later"
- Unified advisory scores (regime score, risk score, fair-value target)
- Buy/sell/rebalance language — use `_BANNED_TERMS` in modules
- `unknown` displayed as `0`
- Mock/demo data as sole production proof (GOV-003, QA-004)

## 4. Rename & liability rules (institutional batches)

- Intelligence → Tracker/Monitor/Context when advisory implied
- Risk → Exposure Metrics (user assesses risk)
- Fair-value → Ratio + Historical percentile
- Engine/Compass → Monitor/Context/Layer

## 5. Architecture patterns

```
bd_platform/<module>.py
  _FEATURE_IDS, _SEED_PATH, _METHODOLOGY_VERSION
  build_*_panel(), *_status(), run_reconciliation_tests()
  _BANNED_TERMS, build_dependencies_block()

data/<module>_seed.json
platform_api.py → /api/platform/intelligence-ledger/...
templates/ + static/js/ → user surface
tests/test_<module>_batch.py
docs/features/<MODULE>.md
```

Register in `intelligence_ledger_hub` catalog automatically via `platform_api.py` routes.

## 6. Evidence classes (never conflate)

| Class | When |
|-------|------|
| BACKTESTED | Seed panels, historical replay |
| SIMULATED | Paper trades, synthetic books |
| SHADOW_LIVE_FORWARD | Live oracle/signals pre-outcome |
| PRODUCTION_VERIFIED | Post-launch with `BLACKDARK_PRODUCTION=true` |

Use `bd_platform.institutional_standards.wrap_intelligence_response()`.

## 7. User journeys (must stay connected)

| Journey | Entry |
|---------|-------|
| Decision | `/dashboard` — Trust Pulse, oracle |
| Platform tools | `/platform` — 40-point hub |
| Intelligence | `/intelligence-ledger` — 109+ modules |
| Institutional | `/institutional`, `/launch-center` |
| CAP646 | `/cap646` |

New features MUST link from hub or launch center; never API-only.

## 8. Testing (mandatory before merge)

```bash
.venv/bin/python -m pytest tests/test_<module>_batch.py -q
.venv/bin/python -m pytest tests/test_intelligence_ledger_hub_batch.py -q
```

GUI changes: verify in browser using the local development server.

## 9. Git & PR

- Branch: `cursor/<descriptive-name>-e85e`
- Commit per logical change; push; PR with evidence screenshots/video
- Base branch: latest feature branch in stack

## 10. External / human-only (do NOT block engineering on these)

- Pentest attestation, live PSP keys, SOC2 auditor, WAF/CDN operator
- Mark `EXTERNAL EVIDENCE` in readiness reports; ship engineering-ready product

## 11. Implementation checklist (copy per feature)

- [ ] Audited existing code — no duplicate logic
- [ ] Formula/version documented
- [ ] Banned terms enforced
- [ ] Stale/missing data visible
- [ ] API routes wired
- [ ] UI surface exists
- [ ] Tests pass
- [ ] Docs written
- [ ] Hub catalog includes module

---

**Programmatic reference:** `bd_platform/institutional_standards.py`  
**Governing docs:** `docs/governing/INSTITUTIONAL_GOVERNING_REFERENCE.md`, `docs/governing/DATA_PLATFORM_GOVERNING_REFERENCE.md`
