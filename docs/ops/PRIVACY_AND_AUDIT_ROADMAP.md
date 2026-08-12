# Privacy Technical Controls & Admin Audit Roadmap

**Findings:** `F-COMP-01`, `F-COMP-02`  
**Classification:** Repository roadmap + partial controls; full privacy program / SIEM = counsel + buyer ops.

## Present (repo)

- Session cookie hardening (P1)
- Admin API key / MFA paths
- Soft Launch vs strict production guard
- Log hygiene rules (no secret echo) in setup scripts
- Public vs whale evidence pack redaction surfaces

## MUST_FIX_PRE_ACQUISITION (docs / design — autonomous)

| Control | Status |
|---------|--------|
| Data categories inventory | Documented in data room (`docs/data-room/DATA_CATEGORIES.md`) |
| Retention defaults | Soft Launch ephemeral; prod Postgres retention policy buyer-owned |
| Deletion request path | Operator runbook stub — legal execution EXTERNAL |
| Admin audit events | Application logs for admin actions — not immutable SIEM |

## EXTERNAL / POST-CLOSE

- Formal DPIA / DPA
- Immutable WORM audit shipping to SIEM
- Counsel privacy opinion
