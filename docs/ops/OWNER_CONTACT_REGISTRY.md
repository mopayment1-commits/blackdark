# Owner Contact Registry

**Purpose:** Eliminate founder-hardcoded contacts from operational docs.  
**Finding:** `F-XFER-02`

| Role | Placeholder | Set by buyer / operator |
|------|-------------|-------------------------|
| Primary admin email | `YOU@example.com` | Identity with `/api/auth` admin + MFA |
| On-call primary | `ONCALL_PRIMARY@example.com` | Pager / phone bridge |
| On-call secondary | `ONCALL_SECONDARY@example.com` | Backup |
| Security contact | `SECURITY@example.com` | Vulnerability intake |
| Billing / PSP owner | `BILLING@example.com` | Stripe/Lemon account holder |
| DNS / cloud owner | `CLOUD@example.com` | Registrar + cloud console |

## Rules

1. Never commit personal founder emails into runbooks.
2. Bootstrap scripts take `--admin-email` explicitly.
3. Buyer fills this registry at handover; treat empty cells as **EXTERNAL** transfer blockers.
