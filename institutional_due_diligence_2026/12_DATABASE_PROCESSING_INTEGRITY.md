# 11 — Database & Processing Integrity (Wave 8)

**Generated:** 2026-09-10T23:50:00Z

## Findings
- **WF-017** P0: Dual-schema architecture (database.py ~60 tables vs Wave-01 17 migrations)
- **WF-018** P2: Duplicate migration 004/010 both CREATE de_funding_rates
- **WF-019** P2: migrate.py _REQUIRED_TABLES omits exchange_flow_labels (017)
- **WF-020** P1: funding_rates REAL vs de_funding_rates DECIMAL type drift

Alembic: 1 revision, documented non-authoritative.

**Wave 8 CLOSED:** Schema inventory complete; production schema unity NOT VERIFIED.
