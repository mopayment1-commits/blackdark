# BLACKDARK SECURITY CERTIFICATION

**Generated:** 2026-08-11T21:57:27Z  
**Branch:** `cursor/institutional-hardening-120d`  
**PR:** https://github.com/mopayment1-commits/blackdark/pull/58  

## Access limitation

GitHub Code Scanning Alerts API returns **HTTP 403** for this agent token  
(`Resource not accessible by integration`). Alert **numbers** on `main` cannot be
enumerated programmatically until a human pastes them or grants `security_events` read.

User-stated current state on `main`: **6 OPEN** CodeQL alerts including HIGH  
clear-text logging and improper code sanitization.

## Evidence-based remediation on this branch (vs `origin/main` @ `5929258`)

| Finding class | Root cause on main tip | Fix on this branch | Status |
|---|---|---|---|
| Clear-text logging (`py/clear-text-logging-sensitive-data`) | `scripts/setup_stripe_production.py` printed `secret.startswith(...)` / API bodies | Livemode via `live_label`; checklist uses `_is_set` booleans; no body dumps | FIXED in branch |
| Clear-text logging / credential echo | `scripts/activate_infra.py` printed Vault dev token `blackdark-dev-root` | Removed token from stdout | FIXED in branch |
| Clear-text storage | `scripts/setup_stripe.py` wrote `STRIPE_SECRET_KEY` into `.env` | Private `keys/stripe.secrets.env` via `write_private_text`; strip legacy `.env` secret lines | FIXED in branch |
| Improper sanitization / DOM XSS | `templates/coin.html` stats via `esc()`+`innerHTML`; chat `innerHTML` | DOM `textContent` / `createTextNode` only | FIXED in branch |
| Prior 18-alert closure suite | Historical High XSS/logging/workflows | Still gated by `tests/test_codeql_18_closure.py` | VERIFIED by tests |

## Divergence

| Ref | Relation |
|---|---|
| `main` @ `5929258` | Still contains stripe clear-text logging + vault token echo + coin stats innerHTML |
| PR #58 tip | Contains institutional hardening + this CodeQL closure pass |
| CodeQL on `main` | Last green run `31531166944` on `5929258` — **does not** include these fixes |

## Local verification (this tip)

- Broader unit suite: **535 passed / 0 failed** (4 load/network deselected)
- Security regression tests: `test_codeql_*`, authz, session, XSS — **PASS**

## Cannot certify yet

Open alert count on GitHub `main` after merge is **unverified** without Alerts API or human paste.  
Therefore FINAL SECURITY VERDICT cannot be **VERIFIED COMPLETE**.

## External blockers

1. Human paste of the 6 open alert rows (number/severity/rule/file/line) **or** grant code-scanning read.
2. Merge fixes to `main` and wait for CodeQL default-branch analysis to close alerts.
3. Sonar AA / `SONAR_TOKEN` / `SONAR_CI_ANALYSIS` remain separate institutional blockers (not CodeQL).
