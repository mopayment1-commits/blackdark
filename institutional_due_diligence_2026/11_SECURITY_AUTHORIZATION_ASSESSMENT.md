# 10 — Security Assessment (Wave 7)

**Generated:** 2026-09-10T23:50:00Z

## Positive Patterns (code-level)
- CSP nonce + strict-dynamic in security_middleware.py
- CSRF protection on cookie mutations
- Production SESSION_TOKEN_PEPPER required

## Findings
- **WF-007** P1: Hardcoded secret pattern heuristics (7 hits) — manual review required
- **WF-015** P1: `/api/analytics/event` accepts caller-supplied user_id without auth decorator
- **WF-016** P2: Dev-default session pepper when env unset (blocked in prod)

## API Auth Surface (Wave 9 overlap)
- 196/304 router endpoints lack auth Depends in signature — NOT VERIFIED intentional

**Wave 7 CLOSED:** Static review; penetration/IDOR full matrix NOT VERIFIED.
