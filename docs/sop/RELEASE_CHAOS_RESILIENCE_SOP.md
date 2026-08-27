# SOP #31 — Chaos / Failure-Injection Resilience (Every Release)

**Type:** Infrastructure safety practice — NOT a user-facing feature.  
**Goal:** Verify fail-closed behavior under real dependency failures. In crypto: **stop rather than emit wrong signals**.

## When to run

- Before every production release
- After changes to DB, Redis, external API connectors, oracles, fee/gas paths
- After circuit breaker or fallback logic changes

## Scope (controlled experiments only)

| Dependency | Failure mode | Expected behavior |
|------------|--------------|-------------------|
| Postgres | Dead host / pool exhausted | Readiness fails; no invented DB state |
| Redis | Missing under viral mode | Disclosed degradation; no fabricated rate-limit state |
| Fee matrix | Unknown venue | `None` — missing ≠ zero |
| Gas oracle | Fetch failure | Empty cache; no invented gas price |
| External API | Timeout / 5xx / circuit open | Stale cache OR `fail_closed`; no live invented data |
| Circuit breaker | 3 consecutive failures | Circuit OPEN; block live calls |

**No uncontrolled production blast radius.** All experiments run in CI/staging or pytest simulation.

## Procedure

### 1. Run chaos gate

```bash
python scripts/release_chaos_gate.py
```

This executes `tests/test_rc2_chaos_resilience.py` + `tests/test_ingestion_circuit_breaker.py` and records results.

### 2. Review experiment report

Output: `data/release_engineering/chaos_experiments.jsonl`

Each row includes:

- `experiment_id`, `timestamp`, `commit_sha`
- `pass_fail` per scenario
- `recovery_proven` (where applicable)
- `data_integrity` (no corruption / no invented truth)
- `critical_defects_open` count

### 3. Fail-closed verification (crypto-critical)

When upstream is unknown or circuit is open:

- Oracle/gas/fee paths return `None` or `DATA_STATE_UNKNOWN` — **never fabricated values**
- Ingestion connectors return stale cache OR `ok: false` with `fail_closed: true`
- Decision surfaces disclose degraded state — no silent wrong signals

### 4. Close Critical/High defects

Release blocked if any open Critical/High defect from chaos experiments.

## Acceptance criteria

- [ ] No uncontrolled production blast radius
- [ ] Fail-closed on critical paths (no wrong signals)
- [ ] No data corruption
- [ ] Recovery proven (circuit half-open → success resets)
- [ ] Repeatable experiments (pytest + recorded JSONL)
- [ ] Critical/High defects closed before release

## CI integration

Chaos pack runs in `.github/workflows/ci.yml` (`test_rc2_chaos_resilience.py`). Release gate adds connector circuit-breaker tests.
