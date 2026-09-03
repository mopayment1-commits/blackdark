# Production URL correction (2026-09-03)

## Authoritative production URL

`https://blackdark-production.up.railway.app`

## Wrong URL used in recent closure reports

`https://blackdark-web-production.up.railway.app` → **HTTP 404 Application not found** (verified 2026-09-03).

## Was this a recent domain change?

**No.** Repository SSOT always used `blackdark-production`:

| Source | URL |
|--------|-----|
| `.env.production.example` | `blackdark-production.up.railway.app` |
| `DEPLOY.md`, `LAUNCH_GUIDE.md`, `WAVE_00_HARDENING.md` | `blackdark-production` |
| `gtm_service.py`, `scripts/setup_stripe_production.py` | default `blackdark-production` |
| `browser_extension`, load-test scripts | `blackdark-production` |

`blackdark-web-production` first appeared in **closure-agent commits on 2026-09-02**:

- `ece7dad` — `docs/GET_ENTITLEMENT_PRODUCTION_CLOSURE.json`
- `63a40c3` … `efe55a8` — pentagonal/supplemental closure scripts and JSON artifacts

That hostname was **never** the Railway-generated domain in deploy docs; it was introduced by mistake in pentagonal closure tooling (`PRODUCTION_URL` constant) and copied into generated evidence JSON. Tests documented against `blackdark-web-production` were **not** valid live probes against production at documentation time (domain returns 404).

## Impact on prior live evidence

| Artifact | Reliable? | Notes |
|----------|-----------|-------|
| `GET_ENTITLEMENT_PRODUCTION_CLOSURE.json` | **No** (URL wrong) | Re-run on `blackdark-production` — see `PRODUCTION_LIVE_VERIFICATION_2026-09-03.json` |
| `PENTAGONAL_HERO_CLOSURE_REPORT.json` live probes | **No** (URL wrong) | Re-run required |
| `SUPPLEMENTAL_CLOSURE_REPORT_1_18.json` item_15 | **No** (URL wrong) | Re-run required |
| Older audits (`WAVE_00`, `PHASE_01`, load tests) | **Yes** | Used correct URL |

## Remediation

- `PRODUCTION_URL` in closure scripts corrected to `blackdark-production`.
- Fresh live verification: `docs/PRODUCTION_LIVE_VERIFICATION_2026-09-03.json`.
