# Financial Data Security Incident Playbook

**Control:** FDS-21  
**Version:** fds-financial-incident-v1  
**Audience:** Security, billing, and privacy on-call

## Scope

Financial-data incidents covered:

| Type | Data class | Default severity |
|------|------------|------------------|
| PAN discovered in controlled storage | FDS-C2 | SEV-1 |
| CVV/CVC/PIN/SAD discovery | FDS-C1 | SEV-1 |
| Leaked financial API secret | FDS-C4 | SEV-1 |
| Exposed webhook signing secret | FDS-C4 | SEV-1 |
| Unauthorized financial export | FDS-C5 | SEV-1 |
| Bank credential exposure | FDS-C3 | SEV-1 |
| Privileged unauthorized financial access | FDS-C5 | SEV-1 |
| Financial data in logs/analytics/AI | FDS-C5 | SEV-1 |
| Compromised payment integration | FDS-C6 | SEV-1 |

## Lifecycle

Every incident follows:

1. **DETECT** — automated scanner, DLP, audit alert, or drill
2. **CONTAIN** — freeze export paths, disable affected integration
3. **PRESERVE EVIDENCE** — tamper-evident logs, request IDs, audit chain
4. **REVOKE / ROTATE** — sessions, API keys, webhook secrets, PSP keys
5. **SCOPE** — tenant/user blast radius, affected data classes
6. **ERADICATE** — purge prohibited data, remove exposure vector
7. **RECOVER** — restore service with rotated credentials
8. **ESCALATE / NOTIFY** — privacy lead, DPO, PSP per legal requirement
9. **POST-INCIDENT REVIEW** — mandatory before closure
10. **CONTROL IMPROVEMENT** — regression test or policy update

## Rules

- **Never** store secret values, PAN, or SAD in incident records.
- Record only: incident type, severity, affected class, scope, timestamps, credential *types* affected, evidence references.
- Hosted checkout architecture must be preserved — do not reintroduce card fields.

## Runnable drill

Synthetic drills live in `fds_retention_incident/incident_drill.py`. Run:

```bash
python -m pytest tests/test_fds_retention_incident_supply_chain.py -q -k incident
```

Drill PASS requires full lifecycle completion — markdown alone is insufficient.

## Escalation

| Severity | Response |
|----------|----------|
| SEV-1 | Immediate page, war-room, freeze financial export |
| SEV-2 | 15m ack, mitigate, postmortem |
| SEV-3 | Next business day |

See also: `docs/ops/INCIDENT_RESPONSE.md` for general ops runbook.
