# Public Accuracy Ledger (#1065)

**Standalone Trust Core module** — immutable public publication layer fed one-way from internal #987 ledger.

## Public surfaces

| Surface | Auth | Description |
|---------|------|-------------|
| `GET /trust/ledger` | None | Errors-first public view |
| `GET /api/trust/ledger` | None | Same JSON API |
| `GET /api/trust/ledger/export` | None | Downloadable data + SHA-256 checksum |
| `GET /api/platform/trust/ledger/status` | None | Module status |
| `GET /api/platform/trust/ledger/export` | None | Platform export alias |

## Policy

- **WORM store** — append-only at `data/public_accuracy_ledger/worm_publication.jsonl`
- **Errors-first** — default view shows latest losses, not cherry-picked wins
- **Outcomes** — `win` · `loss` · `unresolved` · `abstained` only (no "partially correct")
- **Calibration** — Brier score · hit rate · false positive rate · sample size (no metric without sample size)
- **One-way feed** — #987 → #1065 only; no reverse curation

## Integrations

#987 Internal Ledger · #931 Claims Verification · #1064 Falsifiability · #1021 Epistemic Humility · #1030 Live Badge · #1066 Timestamping

## Legal note

"This is our record" — not a claim to be the best platform. Marketing protected by truth.
