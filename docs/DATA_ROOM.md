# BLACKDARK Data Room

Committee-facing index for acquisition / allocator diligence.

## Canon (read first)

| Doc | Purpose |
|-----|---------|
| `docs/CANONICAL_BINDING.md` | Binding product definition |
| `docs/TRUST_OS_VALUE_LAYERS.md` | Four value layers |
| `docs/HEROES_STRATEGY_BINDING.md` | Six heroes quality bars |
| `docs/STRATEGIC_CORRECTION_BINDING.md` | Rejected inflation (ARENA/Neuro/15 sections) |
| `ARCHITECTURE.md` | Runtime / deploy index |

## Prove-it surfaces (live)

| Surface | URL |
|---------|-----|
| Public Accuracy Ledger | `/oracle-accuracy` |
| Emerging Fund Terminal | `/b2b#fund-terminal` |
| Anti-Hype Compliance | `/compliance` |
| Public developer docs | `/docs` |
| Trust OS manifest | `/api/trust-os` |
| Execution closure | `/api/execution/closure` |
| 60s acceptance | `/api/acceptance/60s` |
| Scale readiness | `/api/scale/readiness` |
| Security posture | `/api/security/status` |
| Evidence pack (public summary) | `/api/b2b/evidence-pack/public-summary` |
| Evidence pack (Whale) | `/api/b2b/evidence-pack` |

## Ops honesty

- Soft Launch SQLite ≠ institutional HA.
- Fernet vault ≠ ISO 27001 / SOC 2 certificate.
- High concurrency is **code-enabled**; **proven** only after a signed Postgres+Redis multi-worker row in `docs/LOAD_TEST_RUN_LOG.md`.
- MFA (TOTP) and OAuth2 are engineering controls when configured — not a compliance certificate.

## Human-only remaining

See `docs/DEFERRED_HUMAN_STEPS.md` (Glass Box announce channel, founder cold confirm on deployed URL, signed HA load row).
