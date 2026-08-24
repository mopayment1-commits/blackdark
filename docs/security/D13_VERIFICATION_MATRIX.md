# D-13 Security Verification Matrix

**Defect:** D-13 — Security verification (SAST, auth abuse, CI gates)  
**Status:** CLOSED (PASS WITH RISK)  
**Last updated:** 2026-08-24

## In-repo controls

| Control | Implementation | Test / CI |
|---------|----------------|-----------|
| Dependency audit | `.github/workflows/security.yml` → `pip-audit` | CI on push/PR |
| SAST (Python) | `bandit -r . -x tests,venv` | CI `bandit` job |
| Auth abuse | `verify_admin_key`, session token hashing | `tests/test_d13_auth_abuse.py` |
| Security headers | `security_middleware.py` | `tests/test_security_hardening.py` |
| Production guard | `production_guard.py` | `tests/test_critical_ops_closure.py` |
| Rate limits | `security_middleware.py`, `viral_capacity.py` | `tests/test_wave_00_hardening.py` |
| ZAP baseline (optional) | `scripts/run_wave_00_zap.sh` | Manual / scheduled |

## Auth abuse scenarios covered

| Scenario | Expected | Test |
|----------|----------|------|
| Empty admin key | 401 / reject | `test_admin_key_rejects_empty` |
| Wrong admin key | reject | `test_admin_key_rejects_empty` |
| Session token storage | SHA-256 hash only | `test_session_token_not_reversible` |
| Cross-tenant read | 403 when enforced | `tests/test_d06_institutional_api.py` |

## EXTERNAL EVIDENCE (not claimed in-repo)

- Independent penetration test report
- SOC2 Type II / ISO 27001 certification
- Bug bounty program operational evidence

## Certification

**PASS WITH RISK** — automated gates pass; human pentest and formal certification remain external.
