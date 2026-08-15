# BLACKDARK Transferability Pack

Audience: buyer engineering team taking operational ownership of BLACKDARK.

## Deploy

1. Python 3.11+, Postgres, Redis.
2. Configure secrets via environment / vault — never commit secrets.
3. `alembic upgrade head` then start `dashboard` / API workers.
4. Soft Launch must never waive Postgres/billing/security in `ENV=production`.

## Configure

- SSO: OIDC JWKS + SAML + SCIM under `/api/institutional`.
- Venues/providers: adapters + `canonical_adoption` mapping required.
- Fee matrix: unknown fees fail closed (never invent `0`).

## Operate / Monitor

- Health: readiness, provider health, stream freshness (`stream_freshness_truth`).
- Canonical status: `/api/institutional/canonical/status`
- OMS: `/api/institutional/oms/*`
- Decision brain: `/api/institutional/decision-intelligence/*`
- Risk: `/api/institutional/risk/*`
- Super Terminal: `/api/institutional/super-terminal`

## Debug / Recover

- Stale streams never advertise LIVE (`fanout_safe` / lifecycle manager).
- OMS reconcile compares venue fills; mismatch is recorded fail-closed.
- Flash-crash / risk aggregate blocks unsafe execution.

## Rotate secrets / add venue

1. Rotate via secrets manager; restart workers.
2. Add venue adapter → `adopt_venue` / `adopt_symbol` / `adopt_order_books`.
3. Prove freshness + failure behavior with negative tests.

## Financial / Risk / Decision truth

- Financial: `fee_matrix`, `arbitrage_engine`, `executable_edge_truth` — UNKNOWN → fail closed.
- Risk: `risk_intelligence.full_risk_architecture` feeds Decision + OMS + Portfolio + Whale.
- Decision: `decision_intelligence_engine` + graph + memory + continuous learning + typed confidence.

Documentation here reflects implementation in-repo; marketing COMPLETE labels are not evidence.
