# BLACKDARK SECURITY CERTIFICATION

**Generated:** 2026-08-11T23:58:00Z  
**Branch:** `cursor/institutional-hardening-120d`  
**Tip SHA:** (see git HEAD after push)  
**PR:** https://github.com/mopayment1-commits/blackdark/pull/58  

## Access limitation

GitHub Code Scanning Alerts API returns **HTTP 403** for this agent token.  
User-confirmed state on `main`: **6 OPEN** CodeQL alerts:

- 4 High: Clear-text logging of sensitive information
- 2 Medium: Improper code sanitization

## Mapping: main alerts → tip fixes

| # | Class | Main root cause | Tip fix | Status |
|---|---|---|---|---|
| 1–2 | High clear-text logging | `scripts/setup_stripe_production.py` printed secret-derived / API body | `live_label` + `_is_set` booleans; no body dumps | FIXED on tip |
| 3–4 | High clear-text logging | `scripts/activate_infra.py` Vault token / password echo | Removed from stdout | FIXED on tip |
| 5 | Medium improper sanitization | `templates/coin.html` custom esc → `innerHTML` | DOM `textContent` / `appendChild` | FIXED on tip |
| 6 | Medium improper sanitization | `templates/dashboard.html` chat esc → `innerHTML` | `createTextNode` path | FIXED on tip |

Additional tip hardening (beyond the 6):

- `scripts/setup_production_env.py` writes secrets via `write_private_text`; never `print(block)`
- `bd_platform/vault_client.py` logs event codes only (no `str(exc)`)
- Admin roadmap/plan tables: DOM-only (no `innerHTML`)
- Dashboard half-life clock: `createElementNS` (no raw SVG HTML sink)
- Browser extension popup/content: DOM-only (fixed broken escapeHtml)

## PR CodeQL

PR CodeQL Analyze jobs are green on tip lineage. Main open alerts remain until merge + default-branch reanalysis.

## Residual (honest)

- Default CSP still includes `script-src 'unsafe-inline'` (`CSP_NONCE_MODE` scaffold only) — DEC-0217 PARTIAL
- Residual escaped `innerHTML` sinks remain on some surfaces — DEC-0218 PARTIAL
- Bandit #50 full zero not proven on tip — CF-05 / DEC-0220

## Local verification

- Broader unit suite: **591 passed / 0 failed** (`not load and not network`)
- Security regression: `test_codeql_*`, XSS, authz, session — PASS

## External remaining

1. Merge PR #58 → wait for CodeQL on exact `main` HEAD → confirm open alerts = 0 in Security UI
2. Signed HA multi-worker load (DEC-0407)
3. Acquisition evidence gates A–L (DEC-0501)
