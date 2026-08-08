# 60-Second Grasp — Evidence Log

> Machine probe + agent cold walkthrough. Founder confirm (H3) still required on the **public** URL.

## Machine probe (2026-08-08)

```bash
python scripts/acceptance_60s.py --base http://127.0.0.1:8080
```

Result: `machine_pass=true` (landing, dashboard, ledger, capabilities, trust-os, intent, correction, glass-box, oracle `/quick`).

API: `GET /api/acceptance/60s?base_url=http://127.0.0.1:8080`

## Agent cold walkthrough (local Soft Launch)

| Step | Result |
|------|--------|
| `/` proof-first CTAs | PASS |
| `/oracle-accuracy` Ledger + Glass Box | PASS |
| `/dashboard` intent router | PASS |
| BTC Act/Wait decision | PASS |
| `/capabilities` 4 layers + FalconAI inflation rejected | PASS |

Screenshots (agent session): under `/opt/cursor/artifacts/screenshots/`.

## Remaining human

- **H3:** Founder opens the **deployed** URL cold and confirms the same path.  
- **H2:** Post Glass Box announce drafts (`GET /api/glass-box/announce-drafts`) at chosen datetime/channel.
