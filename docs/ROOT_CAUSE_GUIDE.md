# Root cause & Failure Corpus guide

Engineering memory for incidents, vetoes, and regressions. Use this with `docs/ops/INCIDENT_RESPONSE.md` for live outages and with code/tests for prevention.

## What is the Failure Corpus?

The **Failure Corpus** is BLACKDARK’s append-only **failure intelligence registry**. It records structured events when the platform rejects, kills, or downgrades a path for truth, safety, or governance reasons—not only HTTP 5xx outages.

Typical categories include:

- Truth / constitution vetoes (signals or outputs blocked as untrusted)
- Kill-rate events (decisions explicitly killed rather than shown as live)
- Provenance or freshness downgrades
- Out-of-distribution (OOD) or policy rejections

Implementation: `failure_corpus.py` (`record_failure`, `search_failures`, `corpus_stats`). Each row gets a `failure_id`, `source`, `reason`, `category`, `evidence_class`, optional `meta`, and `recorded_at`.

The corpus **extends** the public kill-rate story (`kill_rate_board.py`); it does not replace it. When applicable, `record_failure` mirrors into the kill-rate board so product and ops surfaces stay aligned.

Launch-57 TEIS support also maintains a scoped store for support-layer failures: `data/launch57_teis_failure_corpus.jsonl` (see `launch57/teis_support_common.py`).

## How it prevents repetition

1. **Write once, query many** — Failures are searchable (`search_failures`, `corpus_stats`) for postmortems, audits, and gate checks (e.g. platform chain, institutional controls).
2. **Link to regression protection** — After root cause is understood, add or extend a **pytest** (or institutional gate test) that would have caught the bug; reference the `failure_id` or category in the test name or docstring when helpful.
3. **Close the loop in process** — Incident close-out (`INCIDENT_RESPONSE.md`): root cause + timeline → control or test update → update runbooks if a new failure mode appeared.
4. **Do not treat “fixed in prod” as enough** — If the same `category` + `source` pattern spikes in `corpus_stats`, treat it as a recurring defect and fix the system, not only the latest row.

Goal: every important failure becomes **documented cause → code or config fix → automated guard**, not tribal memory.

## Where each incident is recorded

| Layer | Location | What goes here |
|-------|----------|----------------|
| **Primary Failure Corpus** | `data/failure_corpus.jsonl` (override: env `FAILURE_CORPUS_FILENAME` via `config`) | All rows from `record_failure()` — canonical engineering registry |
| **Kill-rate mirror** | `data/kill_rate_events.jsonl` | Kill events linked from the corpus (`kill_rate_board.record_kill`) for kill-rate board / public kill-rate narrative |
| **TEIS / Launch-57 support** | `data/launch57_teis_failure_corpus.jsonl` | Support-plane and TEIS-scoped failure rows (separate from the global corpus file) |
| **Human incident process** | `docs/ops/INCIDENT_RESPONSE.md` | Severity, comms, timeline, and close-out for live SEV-1/2/3 — complement the JSONL rows, do not duplicate secrets or PII |

**Programmatic access:** `corpus_stats()` returns totals, breakdowns by `category` / `source`, kill-rate board summary, and the resolved `path` to the corpus file.

**Operators:** For production guard and workflow status (e.g. WF-019/020), see `docs/SECURITY_CLOSURE_STATUS.md` and `GET /api/production/guard` — those are environment readiness checks, not substitutes for logging a specific failure via `record_failure` when the product path vetoes work.
