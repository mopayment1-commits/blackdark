# Incident Response Runbook

**Finding:** `F-OPS-01`  
**Audience:** On-call engineer without founder access

## Severity

| Sev | Meaning | Response |
|-----|---------|----------|
| SEV-1 | Financial truth wrong, auth bypass, data loss, paid path down | Immediate page; freeze execution; war-room |
| SEV-2 | Partial outage, Redis/Postgres degradation, webhook failures | 15m ack; mitigate; postmortem |
| SEV-3 | Non-user-facing defect, docs drift | Next business day |

## First 15 minutes

1. Confirm blast radius: `/health/live`, `/health/ready`, `/api/production/guard`
2. Check recent deploy SHA vs last known-good tag/SHA
3. If financial or auth suspicion → **freeze trading** (`execution_engine.trigger_panic` / admin panic path)
4. Capture evidence: request IDs, `/metrics`, app logs, Postgres/Redis status — **never log secrets**
5. Decide: rollback image vs config fix vs scale-out

## Common failure modes

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| Guard fail | Missing sealed secrets / Soft Launch in strict mode | Fix env; do not bypass |
| 5xx spike | DB pool / Redis / upstream venue | Check Postgres `pg_stat_activity`, Redis `INFO`, rate limits |
| Wrong profit claims | Fee/gas unknown path regressing | Confirm `fee_matrix` None fail-closed; gas oracle stale → None |
| Auth failures | Pepper/session rotation | Rotate carefully; invalidate sessions |
| Webhook 401 | PSP secret mismatch | Rotate webhook secret; replay events |

## Communications

- Internal: on-call primary/secondary from `OWNER_CONTACT_REGISTRY.md`
- External customers: status note only after SEV-1 confirmed; no financial promises
- Security: `SECURITY@example.com` for suspected breach → preserve logs, rotate keys

## Close-out

1. Root cause + timeline
2. Regression test or control update
3. Update this runbook if a new failure mode appeared
