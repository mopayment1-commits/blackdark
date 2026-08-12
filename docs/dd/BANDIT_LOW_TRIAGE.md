# Bandit LOW Triage — External Audit Readiness

**Canonical scan:** `bandit -c .bandit -r .`  
**Result on main tip scan:** HIGH=0 MEDIUM=0 LOW=112

| Test ID | Count | Classification | Rationale |
|---------|------:|----------------|-----------|
| B110 try/except pass | 58 | MIXED | Money modules audited — no bare `except:` pass. Auth reset/profile soft-fail now logs. Remaining are non-critical UI/enrichment degrade paths. |
| B105 hardcoded password | 19 | FALSE_POSITIVE | OAuth token URL strings + test sentinel `'1'` for sqlite bools — not credentials. |
| B311 random | 15 | ACCEPTABLE | Non-crypto shuffle/jitter (ingress jitter, UI). Secrets use `secrets` module. |
| B404 import subprocess | 9 | ACCEPTABLE | Ops/report helpers; not request-path RCE. |
| B603 subprocess | 8 | ACCEPTABLE | Fixed argv lists in ops tooling. |
| B112 try/except continue | 3 | ACCEPTABLE | Loop skip on single bad row (email/execution flatten). |

**REAL DEFECTS fixed this pass:** exception text logging in `arbitrage_service` live-fetch path; password-reset silent swallow now logs type-only.
