# Suspicious Activity Alert Engine (#1019 + #1017)

**Sprint 1 · Merged into Session/Account Security · NOT standalone**

Rule-based real-time alerts for early account takeover detection.

## Triggers (5)

1. Login from new IP/geolocation
2. Password change
3. 2FA disable/change (critical severity)
4. API key modification
5. Role/permission change

## Alert flow

Event → evaluate → alert ≤30s → email + in-app + webhook → ops escalation (#1017)

User message template:
> "نشاط مشبوه: [الحدث] من [الموقع] في [الوقت]. إذا لم تكن أنت، اضغط 'تجميد الحساب'."

## Account freeze

User-initiated freeze: global logout + session kill + API key suspension.

## Location whitelist

Legitimate travel: whitelist location for 7 days (logged).

## API

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /api/platform/suspicious-activity/status` | Public | Policy status |
| `GET /api/platform/suspicious-activity/gate` | Public | Production gate |
| `POST /api/platform/suspicious-activity/freeze` | User | Freeze own account |
| `POST /api/platform/suspicious-activity/whitelist-location` | User | Whitelist location 7d |

## Integrations

- #1019 Session Security — auth events source
- #1017 Incident Response — confirmed takeover playbook
- #1038 Activity Audit — append-only alert trail
- #1033 2FA — disable = critical alert
- #1023 GDPR — breach notification if needed
