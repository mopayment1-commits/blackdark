# BLACKDARK Security Certification (tip)

**Branch:** `cursor/institutional-hardening-120d`  
**Bind evidence to the tip SHA of the commit that lands this file.**

## CodeQL / main alerts (mapped)

| # | Class | Surface | Tip status |
|---|---|---|---|
| 1–4 | Clear-text logging | Stripe/Vault/setup scripts | FIXED on tip (no secret `print` / vault event-code logging) |
| 5 | Improper sanitization | `templates/coin.html` | FIXED — DOM / no unsafe `innerHTML` |
| 6 | Improper sanitization | dashboard chat | FIXED — `createTextNode` path |

PR CodeQL (python/js/actions) must stay green on tip checks. Main-branch open-alert count remains **NEEDS_EXTERNAL** for agent (API 403) — founder confirms UI=0 post-merge.

## XSS / CSP (DEC-0217 / DEC-0218)

- Default CSP: `script-src 'nonce-…' 'strict-dynamic'` — **no** `script-src 'unsafe-inline'`
- Middleware mints nonce, injects onto `<script>` tags, loads `/static/js/csp_events.js`
- HTML `on*` handlers removed → `data-bd-*` binder
- Exploitable sinks closed: discipline DOM-only; whale funding escaped; `esc(safeUrl(...))` for href attrs
- Regression: `tests/test_xss_sink_hardening.py`, `tests/test_security_hardening.py`

## Bandit (CF-05 / DEC-0220)

- Tip scan (`bandit -c .bandit`): **HIGH=0 MEDIUM=0** (LOW residual ~111)
- PR #50 remains CONFLICTING — **do not merge**; HIGH/MEDIUM intent selectively ported
- Helpers on tip: `sql_safety.py`, `path_safety.py`, `.bandit`

## Residual / external

1. Founder confirms main CodeQL open alerts = 0 after merge
2. Acquisition READY founder gates (H3, live PSP, Glass Box, counsel/WAF/pentest)
3. Bandit LOW cleanup (non-blocking quality debt)
