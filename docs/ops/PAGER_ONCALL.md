# Pager / On-Call Integration Template

**Finding:** `F-OPS-03`  
Wiring to a specific vendor is buyer EXTERNAL; this is the repository contract.

## Suggested alert routes

| Signal | Source | Page? |
|--------|--------|-------|
| `/health/ready` fail > 2m | uptime check | SEV-1/2 |
| `/api/production/guard` fail in prod | cron synthetic | SEV-1 |
| Postgres connectivity | health / logs | SEV-1 |
| Redis fail under `VIRAL_MODE` | health/viral | SEV-2 |
| PSP webhook error rate | billing logs | SEV-2 |
| Panic freeze triggered | app log | SEV-1 notify |

## Buyer actions

1. Choose pager (PagerDuty/Opsgenie/Grafana IR)
2. Point synthetic checks at live URL
3. Fill `OWNER_CONTACT_REGISTRY.md`
4. Attach screenshot/export as EXTERNAL evidence
