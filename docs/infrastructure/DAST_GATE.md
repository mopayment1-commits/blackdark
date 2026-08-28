# DAST Gate — Dynamic Application Security Testing

**Not a standalone product.** Runtime security gate merged into Sprint 0 CI/CD — complements #1042 SAST.

## Purpose

Detect vulnerabilities that static analysis misses: TLS misconfiguration, missing auth on endpoints, credential leakage in responses, security header gaps.

## Tooling

| Tool | Role |
|------|------|
| **passive_http_scan** | Security headers, HSTS, passive baseline |
| **rbac_scan** | Unauthenticated access to protected endpoints (#1022) |
| **credential_leak_scan** | API keys/tokens in responses (#1040) |
| **tls_scan** | TLS/HSTS runtime validation (#1039) |
| **OWASP ZAP** | `scripts/run_wave_00_zap.sh` for deep staging scans |

## Targets

| Environment | Policy |
|-------------|--------|
| **CI** | Local ASGI app smoke (non-destructive) |
| **Staging** | Primary weekly scan target |
| **Production** | Off-peak, read-only paths only — no destructive tests |

## Frequency

| Schedule | Mode |
|----------|------|
| Every PR / main push | `ci` — ASGI local smoke |
| Weekly (Monday 06:00 UTC) | `weekly` — staging URL if configured |
| Monthly | `monthly` — deep authenticated scan |
| Post-deployment | `ad_hoc` — admin trigger |

## Severity Policy

| Severity | Action |
|----------|--------|
| Critical + High (production) | #1017 Incident Response trigger |
| Medium | Ticket for next Sprint |
| Low | Tracked only |

## Rate Limiting

- Throttled to 2 RPS by default (`throttle_rps` in seed)
- Off-peak preferred for production
- Coordinated with #1020 load testing

## APIs

| Endpoint | Purpose |
|----------|---------|
| `GET /api/platform/dast/status` | Policy status |
| `GET /api/platform/dast/gate` | Production gate |
| `GET /api/platform/dast/e2e` | Self-test |
| `POST /api/platform/dast/scan` | Admin on-demand scan |

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `DAST_TARGET_URL` | Staging/production URL for remote scan |
| `DAST_PRODUCTION_READ_ONLY` | `true` — only public read-only paths on prod |
| `DAST_TARGET_ENV` | `production` — enables production incident triggers |
| `DAST_ADMIN_API_KEY` | Authenticated path testing (monthly deep scan) |

## CI/CD

```yaml
# .github/workflows/security.yml → job: dast-gate
python scripts/run_dast_gate.py
```

## Audit

Append-only: `data/dast_scan_audit.jsonl` — 2-year retention.

Suppressions: `data/dast_suppressions.json` — security-lead approval required.

## Integrations

| Ref | Integration |
|-----|-------------|
| #1042 SAST | Static + dynamic = complete coverage |
| #1017 | Critical finding → incident playbook |
| #1039 | TLS 1.3 / HSTS runtime checks |
| #1022 | RBAC privilege escalation probes |
| #1040 | Response credential leakage detection |
| #1020 | Throttled scans — load test coordination |

## Local Development

```bash
python scripts/run_dast_gate.py
DAST_TARGET_URL=https://staging.example.com python scripts/run_dast_gate.py --mode weekly
RUN_ZAP=1 TARGET_URL=https://staging.example.com bash scripts/run_wave_00_zap.sh
```
