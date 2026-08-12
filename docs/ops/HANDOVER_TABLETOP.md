# Handover Tabletop (No Founder)

**Finding:** `F-XFER-01`

Two buyer engineers, 90 minutes, no founder calls.

| # | Exercise | Pass criteria |
|---|----------|---------------|
| 1 | Fresh clone + hash-locked install | venv boots; imports succeed |
| 2 | Soft Launch bootstrap with registry email | `.env.softlaunch.local` created; admin login works |
| 3 | Production guard interpretation | Can explain fail-closed items |
| 4 | Secret file hygiene | Create Telegram/Stripe private files; confirm not in `.env` cleartext |
| 5 | Backup script dry-run | Backup artifact produced against staging DSN |
| 6 | Rollback plan narration | Can point to previous image + panic freeze |
| 7 | Incident SEV-1 drill | Follow `INCIDENT_RESPONSE.md` without founder |
| 8 | Find fee authority | Locate `fee_matrix` + Decimal path; explain unknown → None |

Record date, participants, pass/fail in buyer data room.
