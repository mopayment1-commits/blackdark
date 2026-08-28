# DDoS Protection Layer (#1047)

**Sprint 0 · Infrastructure · NOT standalone · Non-Custodial**

Layered defense ensuring service continuity under deliberate attack.

## Defense sequence

```
DDoS Edge (L3/L4) → WAF (L7) → Security Rate Limit (#1046) → Auth (#1019) → RBAC (#1022) → Service
```

## Layers

| Layer | Implementation |
|-------|----------------|
| Network L3/L4 | Cloudflare / AWS Shield / Fastly |
| Application L7 | WAF + Rate Limiting (#1046) |
| Origin | nginx connection limits + resource pools |

## Failover

Auto-failover to secondary region (#1016 DR) — DNS-based, health-checked.

## Templates

- `deploy/cloudflare/waf-rules.json`
- `nginx/blackdark.conf`
- `docs/CDN_WAF_CHECKLIST.md`

## API

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/ddos-protection/status` | Layer status + edge |
| `GET /api/platform/ddos-protection/gate` | Production gate |
| `GET /api/platform/ddos-protection/e2e` | E2E self-test |

## Audit

`data/ddos_attack_audit.jsonl` — 90-day retention (#1038).

## Integrations

- #1046 Rate Limiting — app-layer gate
- #1017 Incident Response — attack playbook
- #1016 Backup & DR — failover
- #1020 Load Testing — threshold calibration
- #908 Stripe — billing continuity during attack
