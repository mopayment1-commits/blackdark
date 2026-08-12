# BLACKDARK INSTITUTIONAL COMPLETION REGISTER

**PR:** #72  
**Tip:** see `git rev-parse HEAD` on `cursor/95plus-recert-phase0-120d`  
**Rule:** Register never exceeds independent clean-room classifications.

## Implemented this completion loop

| Priority | Deliverable | Evidence |
|---|---|---|
| P0 | Canonical Truth Bus — LIVE→CANONICAL sole production path | `canonical_truth_bus.py`, refresh wired to API |
| P1 | Venue fill lifecycle proof (paper + testnet-ready) | `venue_fill_proof.py` → Intent…Fill→Reconcile→Portfolio→Audit |
| P2 | Postgres/SQLite institutional authority | `inst_*` tables in `database._apply_migrations`, `institutional_store.py` |
| P3 | Decision E2E + Super Terminal unified decision_object | `decision_e2e.py`, Super Terminal `unified_decision` |
| P3 | Whale $5M band + live-book option | `whale_execution_evidence.py` |
| P4 | Ops backup/restore probe | `ops_recovery.py` |
| P4 | B2B alerts dual-write to DB | `b2b_institutional_ops.py` → `inst_alerts` |

## Honest classification (pre clean-room)

VERIFIED_COMPLETE remains **0** until independent clean-room says otherwise.  
Domains moved from scaffold/isolated → **wired PARTIAL with behavioral proofs**.

## APIs added

- `GET /api/institutional/canonical/status` (includes truth bus)
- `POST /api/institutional/venue-fill-proof`
- `POST /api/institutional/decision-e2e`
- `GET /api/institutional/ops/recovery`
- `GET /api/institutional/store/status`
