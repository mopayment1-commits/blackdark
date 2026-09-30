# Railway — Launch-57 CISA environment variables

Set on **web** service (production):

| Variable | Value | Finding |
|----------|-------|---------|
| `ENV` | `production` | — |
| `APP_BASE_URL` | `https://blackdark-production.up.railway.app` | 14, 05 |
| `WEBAUTHN_RP_ID` | hostname from APP_BASE_URL | 05 |
| `USER_MFA_ENROLL_REQUIRED` | `true` | 04 |
| `SECURITY_LOG_RETENTION_DAYS` | `180` | 08 |
| `CDN_WAF_ACTIVE` | `1` after Cloudflare proxy | 19 |
| `CLOUDFLARE_ZONE_ID` | zone id (optional) | 19 |
| `BLACKDARK_RELEASE` | `launch-57` | 10 |
| `AUDIT_SIGNING_KEY` | production secret | ops |

## Post-deploy verification

```bash
export LAUNCH57_PROD_URL=https://blackdark-production.up.railway.app
python scripts/launch57_ops_closure_gate.py
```
