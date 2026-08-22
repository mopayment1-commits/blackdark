# BLACKDARK Support Tiers

**Status:** Operational — published support contacts and escalation paths confirmed

## Published support operations

| Field | Value |
|---|---|
| Support email | MOPAYMENT1@GMAIL.COM |
| Support owner | Project owner/operator |
| Support hours | 10:00 AM – 10:00 PM Cairo Time, daily |
| Urgent escalation | Same support email with subject prefix **URGENT** |

Urgent issues: email **MOPAYMENT1@GMAIL.COM** with a subject line starting with `URGENT` (for example: `URGENT — billing outage`).

## Tiers

| Tier | Channels | Hours | Escalation |
|---|---|---|---|
| Free / Demo | Community docs, `/docs`, email | Best effort within published hours | Standard queue |
| Pro | Email, in-app alerts | 10:00 AM – 10:00 PM Cairo Time, daily | Engineering queue via support email |
| Elite / Quant | Priority email, in-app alerts | 10:00 AM – 10:00 PM Cairo Time, daily | Priority queue; URGENT subject prefix |
| Institutional | Dedicated contact, SLA-backed | Contractual (24×5 baseline) | Named account + URGENT exec escalation |

## Internal artifacts

- `/contact` — published support email, hours, and escalation instructions
- `api/routers/institutional.py` — `GET /api/institutional/support`
- `institutional_assurance.py` — support ticket intake + tier SLAs
- `in_app_alerts.py` — in-app alert inbox
- `docs/DATA_ROOM.md` — institutional diligence index

## Operator configuration

Override via environment when needed:

- `SUPPORT_EMAIL` (default: `mopayment1@gmail.com`)
- `SUPPORT_OWNER` (default: `Project owner/operator`)
- `SUPPORT_HOURS` (default: Cairo hours above)
- `SUPPORT_URGENT_SUBJECT_PREFIX` (default: `URGENT`)
