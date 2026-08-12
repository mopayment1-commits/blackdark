# CSP Production Attestation

**Finding:** `F-SEC-01`

| Control | Required value | Code default |
|---------|----------------|--------------|
| `CSP_NONCE_MODE` | `true` / unset | **Default `"true"`** in `security_middleware.py` |
| Emergency rollback | `CSP_NONCE_MODE=false` | Re-opens `script-src 'unsafe-inline'` — break-glass only |

## Operator attestation (fill at go-live)

| Field | Value |
|-------|-------|
| Environment URL | |
| SHA deployed | |
| `CSP_NONCE_MODE` observed | |
| Attested by | |
| Date (UTC) | |

**Rule:** Soft Launch and Production must ship with nonce mode ON. Setting `false` is an incident-level exception with time-boxed expiry.
