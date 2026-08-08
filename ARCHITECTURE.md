# BLACKDARK — Architecture Index

> **Purpose:** Single entry for maintainability / acquirer DD.  
> **Rule:** This file indexes binding docs — it does not redefine product shape.  
> **Canon:** [`docs/CANONICAL_BINDING.md`](docs/CANONICAL_BINDING.md)

---

## Product shape (locked)

```
User intent (dashboard) → Six Heroes → Quiet engines (~Signal Registry)
                              ↓
                    Public Accuracy Ledger + Decision Certificates
                              ↓
                    Four Trust OS value layers (acquisition framing)
```

| Layer | Surfaces |
|-------|----------|
| Decision Intelligence | `/dashboard`, `/oracle/{symbol}`, `/discipline-mirror` |
| Transparency & Evidence | `/oracle-accuracy`, `/errors` → `#losing`, Glass Box APIs |
| Market / Execution Edge | Arb scanner, Whale S/N, Stealth Advisor (advisory) |
| Institutional Packaging | `/b2b#fund-terminal`, `/compliance`, B2B feed |

---

## Data flow (simplified)

```
CEX/DEX / market adapters
        ↓
Ingestion + live book hub (WS when available; REST fallback)
        ↓
Opportunity / Oracle engines (net-edge · half-life · conflict guard)
        ↓
Decision Certificate + audit hash chain
        ↓
Public Accuracy Ledger (/oracle-accuracy) · private Discipline Mirror
        ↓
Alerts inbox / Telegram (proof-gated) · B2B feed (signed)
```

Storage posture:

| Mode | Database | Notes |
|------|----------|-------|
| Soft Launch | SQLite allowed | Demo only — not an HA claim |
| Production (strict) | **PostgreSQL required** | `DATABASE_URL=postgresql://…` · `SOFT_LAUNCH` unset |
| Secrets at rest | Fernet vault | User exchange keys · model weights HMAC · not ISO cert |

---

## Binding documents

| Doc | Role |
|-----|------|
| [`docs/PRODUCT_CONSTITUTION_AR.md`](docs/PRODUCT_CONSTITUTION_AR.md) | D1–D8 constitution |
| [`docs/CANONICAL_BINDING.md`](docs/CANONICAL_BINDING.md) | Authority hierarchy |
| [`docs/TRUST_OS_VALUE_LAYERS.md`](docs/TRUST_OS_VALUE_LAYERS.md) | Four layers |
| [`docs/HEROES_STRATEGY_BINDING.md`](docs/HEROES_STRATEGY_BINDING.md) | Six heroes |
| [`docs/STRATEGIC_CORRECTION_BINDING.md`](docs/STRATEGIC_CORRECTION_BINDING.md) | Reject inflated pastes |
| [`docs/FULL_ARCHITECTURE_AUDIT.md`](docs/FULL_ARCHITECTURE_AUDIT.md) | Deep audit notes |
| [`docs/MICROSERVICES_ARCHITECTURE.md`](docs/MICROSERVICES_ARCHITECTURE.md) | Service split |
| [`docs/RUNBOOK.md`](docs/RUNBOOK.md) | Ops runbook |
| [`docs/SECURITY_REMEDIATION.md`](docs/SECURITY_REMEDIATION.md) | Security remediation |
| [`docs/GLASS_BOX_OPERATOR_RUNBOOK.md`](docs/GLASS_BOX_OPERATOR_RUNBOOK.md) | One public prove-it event |

---

## Public developer surface

- HTML: `/docs`  
- Public OpenAPI (read/evidence only): `/api/docs/public-openapi.json`  
- Full ops OpenAPI: `/api/docs/openapi.json`  
- Production guard: `/api/production/guard`  
- Security posture: `/api/security/status`  

**Not claimed:** ISO 27001/25010 certificates · HashiCorp Vault as shipped · HA without Postgres+Redis load log.
