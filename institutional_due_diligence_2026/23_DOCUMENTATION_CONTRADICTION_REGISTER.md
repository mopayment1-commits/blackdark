# 20 — Documentation Contradictions (Wave 17)

**Generated:** 2026-09-10T23:50:00Z

## CONTRADICTION_REGISTER

| ID | Docs Say | Code/Audit Says | Status |
|---|---|---|---|
| CON-001 | BATCH07_FINAL_LOCAL_FREEZE=true | Zero-trust: E6 claim only | NOT VERIFIED |
| CON-002 | CI PASS in freeze JSON | Tests not re-run in audit | NOT VERIFIED |
| CON-003 | templates/index.html exists | /app redirects to /dashboard | VERIFIED orphan |

**WF-009** P2: Freeze claims unrevalidated.

**Wave 17 CLOSED:** Contradiction register initialized.
