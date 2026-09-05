# Incident Response Runbook

**Control:** SEC-009 · **Feature:** #829 / #1017 Incident Response Plan  
**Finding:** `F-OPS-01`  
**Module:** `bd_platform/infrastructure_incident_response_security_ops.py`  
**Audience:** On-call engineer without founder access

## Roles (24/7 accessible)

| Role | Responsibility |
|------|----------------|
| **Incident Commander** | Declare severity, coordinate response, authorize isolation + DR trigger |
| **Communications Lead** | User notifications via approved templates — no guaranteed uptime language |
| **Technical Lead** | Execute isolation playbooks, lead investigation |
| **Legal Advisor** | Regulatory guidance for breach/data leak — required within 15–30 min |

## Escalation SLA

| Step | Target | SLA |
|------|--------|-----|
| Automated alert | Monitoring system | Immediate |
| On-call engineer | First responder | **5 minutes** |
| Incident Commander | War-room lead | **15 minutes** |
| Legal Advisor | Breach / data leak only | **30 minutes** |

## Severity

| Sev | Meaning | Response |
|-----|---------|----------|
| SEV-1 | Breach, data leak, auth bypass, paid path down | Immediate page; isolation; DR auto-trigger |
| SEV-2 | Partial outage, Redis/Postgres degradation | 15m ack; mitigate; postmortem |
| SEV-3 | Non-user-facing defect | Next business day |

## Mandatory Scenarios (5 playbooks)

1. **Breach** — kill switch · firewall · tenant isolation · DR trigger · provenance check
2. **Data Leak** — tenant containment · Legal notify · user notice within 1h
3. **Service Outage** — DR auto-trigger · status page · best-effort comms
4. **DDoS** — WAF rules · CDN scale · edge rate limiting
5. **Key Compromise** — vault rotation · session invalidation · billing integrity check

## Isolation Playbooks (tested every 90 days)

| Playbook | Action |
|----------|--------|
| `api_kill_switch` | Disable API write endpoints |
| `firewall_rules` | Block suspicious traffic at edge WAF |
| `db_read_only` | Switch database to read-only mode |
| `tenant_isolation_trigger` | Contain affected tenant — no cross-tenant leak |

## User Notification

- **Critical incidents:** notify within **1 hour**
- **Channels:** email · in-app banner · status page
- **Approved language:** "investigating" · "working to restore" · "best effort"
- **Forbidden:** "guaranteed uptime" · "confirmed immediate restore" · "ضمان" · "مؤكد" · "استعادة فورية"

## First 15 minutes

1. Confirm blast radius: `/health/live`, `/health/ready`, `/api/production/guard`
2. Check recent deploy SHA vs last known-good tag/SHA
3. If breach/auth suspicion → **API kill switch** + freeze execution
4. Capture evidence: request IDs, `/metrics`, logs — **never log secrets**
5. Incident Commander declared; escalate per SLA above
6. Critical incident → **DR playbook auto-triggers** (#828)

## Integrations

| System | Action |
|--------|--------|
| #828 Backup & DR | Auto-trigger DR playbook on critical incidents |
| #945 Provenance | Post-incident lineage integrity check |
| #908 Pay-Per-Request | Billing integrity + idempotency replay protection test |
| #949 Retention | Data leak = incident type under retention governance |

## Audit

- Every incident logged: timeline, actions, decisions, communications, user notifications
- **5 year retention** · append-only · immutable hash chain
- Tenant isolation tested in drills — no cross-tenant recovery leak

## API (admin only)

```
GET  /api/platform/internal/infrastructure/incident-response/status
GET  /api/platform/internal/infrastructure/incident-response/panel
GET  /api/platform/internal/infrastructure/incident-response/runbook/{scenario}
GET  /api/platform/internal/infrastructure/incident-response/escalation
GET  /api/platform/internal/infrastructure/incident-response/isolation-playbooks
GET  /api/platform/internal/infrastructure/incident-response/notification-template/{template_id}
POST /api/platform/internal/infrastructure/incident-response/incident
POST /api/platform/internal/infrastructure/incident-response/escalation
POST /api/platform/internal/infrastructure/incident-response/isolation-drill
POST /api/platform/internal/infrastructure/incident-response/notify
GET  /api/platform/internal/infrastructure/incident-response/audit-trail
GET  /api/platform/internal/infrastructure/incident-response/e2e
```

## Close-out

1. Root cause + timeline in immutable audit log
2. Post-incident provenance + billing integrity checks
3. Regression test or control update
4. Update this runbook if a new failure mode appeared
