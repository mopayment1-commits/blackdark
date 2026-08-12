# BLACKDARK Data Room

Committee-facing index for acquisition / allocator diligence.

**RC2:** Repository-producible artifacts are indexed below. Legal/live/cloud ownership items remain EXTERNAL (never fabricated as PASS).

## Canon (read first)

| Doc | Purpose |
|-----|---------|
| `docs/CANONICAL_BINDING.md` | Binding product definition |
| `docs/TRUST_OS_VALUE_LAYERS.md` | Four value layers |
| `docs/HEROES_STRATEGY_BINDING.md` | Six heroes quality bars |
| `docs/STRATEGIC_CORRECTION_BINDING.md` | Rejected inflation (ARENA/Neuro/15 sections) |
| `ARCHITECTURE.md` | Runtime / deploy index |
| `docs/dd/BLACKDARK_RC1_MANIFEST.md` | Immutable RC1 freeze |
| `docs/dd/BLACKDARK_RC2_REMEDIATION_LEDGER.json` | RC1→RC2 machine-readable ledger |
| `docs/dd/BLACKDARK_RC2_FINAL_CERTIFICATION.md` | RC2 certification report |

## Prove-it surfaces (live)

| Surface | URL |
|---------|-----|
| Public Accuracy Ledger | `/oracle-accuracy` |
| Emerging Fund Terminal | `/b2b#fund-terminal` |
| Anti-Hype Compliance | `/compliance` |
| Public developer docs | `/docs` |
| Trust OS manifest | `/api/trust-os` |
| CSO Priority Chain | `/priority-chain` · `/api/strategy/priority-chain` |
| Zero-Tolerance defects | `/zero-tolerance` · `/api/strategy/zero-tolerance` |
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

## Repository-producible packs (RC2)

| Pack | Path |
|------|------|
| SBOM (CycloneDX) | `docs/data-room/sbom/cyclonedx-python.json` |
| License inventory | `docs/data-room/licenses/` |
| Buyer handover | `docs/ops/BUYER_HANDOVER_PACK.md` |
| Incident / DR / secrets | `docs/ops/INCIDENT_RESPONSE.md`, `BACKUP_RESTORE.md`, `SECRET_ROTATION.md` |
| Env / ownership maps | `docs/ops/ENV_VAR_REGISTRY.md`, `SERVICE_OWNERSHIP_MAP.md`, `EXTERNAL_VENDOR_MAP.md` |
| Account ownership template | `docs/ops/ACCOUNT_OWNERSHIP_SCHEDULE.md` (**EXTERNAL fill**) |
| CSP / CORS reviews | `docs/ops/CSP_PRODUCTION_ATTESTATION.md`, `CORS_ALLOWLIST_REVIEW.md` |
| NOTICE / third-party | `NOTICE`, `THIRD_PARTY_NOTICES.md` |
| Load evidence (MEASURED) | `docs/LOAD_TEST_RUN_LOG.md` |
| Security | `SECURITY.md`, `docs/SECURITY_HARDENING.md`, `docs/BLACKDARK_SECURITY_CERTIFICATION.md` |
| Financial correctness tests | `tests/test_rc2_financial_truth.py`, fee/money suites |
| Chaos / resilience tests | `tests/test_rc2_chaos_resilience.py` |

## Human-only remaining

See `docs/DEFERRED_HUMAN_STEPS.md` and RC2 EXTERNAL list (PSP, CodeQL UI, counsel, Sonar New Code admin, branch protection, WAF/pentest, account ownership fill-in, live restore drill, founder 60s).
