# Zero non-human deferrals (binding)

**Rule:** After this commit, the only remaining deferred items are **HUMAN_OPS** listed in [`DEFERRED_HUMAN_STEPS.md`](./DEFERRED_HUMAN_STEPS.md).

## Meaning of “تنفيذ كامل”

Code-complete to the highest practical engineering bar:

- Agreed Sat/Sun product decisions are implemented on this branch.
- Quality gates (Ruff/pytest/CodeQL hygiene ports) are addressed in-repo.
- Surfaces are user-visible (Language works, Login/Sign up/Pricing chrome, lenses division, institutional inquiry form).
- Status is **review + merge only** — not “finish later in another agent pass.”

## Explicitly NOT deferred in code anymore

| Former PARTIAL | Closure on this branch |
|---|---|
| PR #33 vs main visibility | **MERGED to `main`** (`a08aed7`, 2026-08-09) — founder pulls `main` |
| i18n actually switches UI | Landing/login wired; AR + samples; regression tests |
| Institutional path | `/api/billing/institutional-inquiry` + landing form (sales-led wire/invoice) |
| CodeQL hygiene | Ported vault/sse/coverage/secret scripts + dashboard `esc()` |
| Viral/HA / security absolute claims | Code paths + guards present; live staging/signed load/WAF remain HUMAN_OPS by nature |

## Still HUMAN_OPS only (allowed)

H1 Browser extension merge/load · H2 Glass Box announce clock · H3 founder 60s · HA signed load row · PSP/KYC/webhook secrets · legal counsel · deploy account actions · paid traction evidence.

## Reviewer checklist

1. ~~Merge PR #33 into `main`.~~ **Done** (`a08aed7`).
2. Confirm CI green on the merge commit — **was green at merge**.
3. Founder pulls `main` and verifies Language/Login/Pricing/`/#lenses`.
4. Execute HUMAN_OPS when ready — do not reopen code deferrals without a new decision.
5. Final non-human report: [`FINAL_NONHUMAN_EXECUTION_REPORT_AR.md`](./FINAL_NONHUMAN_EXECUTION_REPORT_AR.md).
