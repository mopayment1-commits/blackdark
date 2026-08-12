# CORS Allowlist Review

**Finding:** `F-SEC-04`

## Implementation

- Module: `security_middleware.py`
- Applied in: `dashboard.py`
- Env: `CORS_ALLOWED_ORIGINS` (comma-separated) + `APP_BASE_URL`
- Credentials: `allow_credentials=True`
- Wildcard `*` origins: **rejected**

## Default when empty

Localhost development origin (`http://127.0.0.1:8080` / configured app base).

## Production checklist

1. Set `APP_BASE_URL=https://<canonical-host>`
2. Set `CORS_ALLOWED_ORIGINS` to exact browser origins that must call credentialed APIs
3. Do not include marketing sites that do not need cookie APIs
4. Verify preflight from an unlisted origin fails
5. Record reviewed origins below

| Origin | Purpose | Approved |
|--------|---------|----------|
| | | |

Residual risk if misconfigured: cross-origin credentialed API access from unexpected sites.
