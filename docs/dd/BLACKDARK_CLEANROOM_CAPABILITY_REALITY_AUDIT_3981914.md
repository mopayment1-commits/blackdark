# BLACKDARK CLEAN-ROOM CAPABILITY REALITY AUDIT

**Auditor posture:** Independent adversarial clean-room. Docs, remediation ledgers, `COMPLETE`
labels, `product_complete` self-labels, commit messages, the `BLACKDARK_INSTITUTIONAL_COMPLETION_REGISTER`,
the `institutional_gate_cert.py` self-probe, desired scores, and green test counts are **NOT** evidence.
Only runtime probes, wiring inspection, negative paths, and observed failure behavior are.

The goal was to **disprove BLACKDARK completeness**. Every "institutional depth" / "DB authority" /
"fill proof" / "decision E2E" claim introduced since `2af4e5f` was re-tested behaviorally at this exact SHA.

---

```
EXACT SHA AUDITED:  3981914b1b4604d739b06e1b4a7ad05124571728
WORKTREE HEAD:      3981914b1b4604d739b06e1b4a7ad05124571728   (MATCH — detached worktree)
BRANCH TIP (context): cursor/95plus-recert-phase0-120d
TIP SUBJECT:        "Fix OMS file/DB sync for dual-write idempotency and test isolation"

HEAD-MISMATCH NOTE (main workspace):
  Mid-audit, primary /workspace HEAD drifted to 3c01c26
  ("Wire Super Terminal and whale defaults through Canonical Truth Bus").
  Per audit rules, product probes were re-executed in a detached git worktree
  pinned to 3981914 so evidence below is NOT contaminated by later commits.

DELTA SINCE 2af4e5f AUDIT (64/100):
  24a68a1  Add independent clean-room capability reality audit for 2af4e5f (NOT COMPLETE, 64/100)
  9e29083  Fix non-hermetic decision calibration; live-anchor Super Terminal books
  aa57acc  Implement institutional depth: truth bus, DB authority, fill proof, decision E2E
  3981914  Fix OMS file/DB sync for dual-write idempotency and test isolation   <-- tip
```

Code delta since `2af4e5f` is three product commits (plus one audit-doc commit):
- **`aa57acc`**: new `canonical_truth_bus`, `institutional_store`, `venue_fill_proof`, `decision_e2e`,
  `ops_recovery`; OMS/decision/memory dual-write hooks; whale $5M band; APIs/tests.
- **`9e29083`**: `evaluate_decision(use_calibration=False)` hermetic default; Super Terminal
  prefer-live OKX anchor **with `synthetic_fallback` ≈100.0 retained**.
- **`3981914`**: OMS file-cache idempotency before DB recovery; cold-mirror hydrate from DB;
  cancel/replace dual-write; test `DB_PATH` isolation.

---

## INVENTORY COUNTS

| Metric | Count |
|---|---:|
| Tracked files | 773 |
| Python modules (tracked) | 485 |
| Test files (`tests/*.py`) | 113 |
| Markdown docs under `docs/` | 120 |
| Prior clean-room audits in `docs/dd/` | 7 (… through `2af4e5f`) — this is the 8th |
| `product_complete: True` lines (*.py, excl. tests/docs) | **40** |
| `product_complete: False` lines (*.py, excl. tests/docs) | **30** |

### Classification of the mandatory focus set (24 capabilities + gate-cert layer)

| Classification | Count |
|---|---:|
| VERIFIED_COMPLETE | **0** |
| PARTIAL | **21** |
| SCAFFOLD | **1** (White Label) |
| NOT_IMPLEMENTED | **1** (Jupiter live submit) |
| UNVERIFIED | **1** (scheduled multi-venue *ingestion* / real L2 depth authority) |
| EXTERNAL | **1** (live DR / RPO-RTO proof beyond SQLite copy probe) |

**Register vs reality:** new modules honestly self-label `implementation_class: PARTIAL` /
`verified_complete: false`. That does not make the product COMPLETE. Self-label census remains
**40 True / 30 False** — peripheral modules still over-claim.

---

## MANDATORY RUNTIME PROBES — BEHAVIORALLY TESTED AT 3981914

| # | Probe | Verdict | Behavioral evidence (runtime) |
|---|---|---|---|
| 1 | **`canonical_truth_bus.refresh_live_truth` + `get_live_books(require_live=True)`** | **LIVE TOP-OF-BOOK REACHES BUS (PARTIAL)** | `refresh_live_truth_sync()` → `ok:true, venues:[kraken,okx]`; proof `live_count:2, stale_as_live:0`. `get_live_books(require_live=True)` returned 8-level books with live mids ≈ **63371 (OKX) / 63374 (Kraken)**. **However** bus *reconstructs* bid/ask sizes as `2.0+i` / `1.5+i` around live top-of-book — not venue L2 depth. Live prices yes; real depth authority no. |
| 2 | **Consumers of bus (risk / decision engine / whale / super_terminal)** | **PARTIAL / UNEVEN** | `risk_intelligence` / `decision_intelligence_engine`: **no** `canonical_truth_bus` import — callers must pass depths. `whale_execution_evidence.measure_whale_readiness`: **does** call `get_live_books`, but `require_live=False` by default; on reconstructed books returned `whale_ready:true` and even self-labeled `product_complete:true`. `super_terminal`: **does not** import the bus; uses `probe_okx_book` when available (`book_source:okx_public_live_anchor` this run) and **retains hard-coded ≈100.0 `synthetic_fallback`** plus microstructure sample `[[100.0,…]]`. |
| 3 | **`venue_fill_proof.prove_fill_lifecycle`** | **PAPER ONLY** | Env unset → `dry_run:true, mode:paper_lifecycle, live_fill:false, oms_state:RECONCILE`, history `INTENT→…→ACK→FILL→RECONCILE`. Paper lifecycle works; **no real venue FILL**. |
| 4 | **`institutional_store` + OMS dual-write (isolated tmp DB)** | **SQLITE DUAL-WRITE WORKS (PARTIAL)** | Isolated `DB_PATH` under sandbox: `store_status` → `authority:sqlite`, tables `inst_oms_*` / `inst_audit_events` / … present. `create_intent→submit dry_run→FILL→reconcile` wrote `RECONCILE` to both file mirror and SQLite; cold empty file **hydrated from DB**; idempotency key returned same `order_id`; mismatch reconcile still `ok:false, mismatch:true`. **SQLite dual-write ≠ Postgres HA production authority.** |
| 5 | **`decision_e2e.run`** | **OBJECT EXISTS; NOT VERIFIED_COMPLETE** | Returned `ok:true`, `pipeline:LIVE→CANONICAL→RISK→DECISION→OUTCOME→LEARNING`, `live_venues:[kraken,okx]`, coherent `decision_object` with risk domains, whale, evidence, learning, `graph_id`. Self-labels `product_complete:false, verified_complete:false`. Fed by reconstructed bus books + heuristic confidence — not a live-execution-closed loop. |
| 6 | **`ops_recovery` backup/restore** | **SQLITE COPY PROBE OK** | `prove_sqlite_backup_restore()` → `ok:true, engine:sqlite`, institutional tables readable after copy/reopen. Degrade matrix is declarative. **Not** live Postgres `pg_dump` / RPO-RTO DR evidence. |
| 7 | **B2B alert channels** | **HONEST PENDING-CONNECTOR (PARTIAL)** | Connectors unset: `inbox→status:delivered, transport:in_app_inbox`; `pager/email/slack→accepted_pending_connector, delivered:false, accepted:true`; `webhook→delivery_failed` fail-closed. Inbox still writes `alert_deliveries.jsonl` only — **no** `in_app_alerts` store push. |
| 8 | **Jupiter `execute_swap(dry_run=False)`** | **STILL BLOCKED / NOT_IMPLEMENTED** | `adapter_status` → `implementation_class:NOT_IMPLEMENTED, live_submit_implemented:false`. `execute_swap(..., dry_run=False)` → `mode:blocked, executed:false` (quote path network-fail-closed here; even on quote success code path cannot set `executed:true` without wallet+flag, and final guard remains fail-closed). |
| 9 | **`live_rollout_status` / `prove_multi_venue_live`** | **STILL OK (reporting)** | `prove_multi_venue_live` → `ok:true, live_count:2 [kraken,okx], stale_as_live:0` (Binance HTTP 451). `live_rollout_status` → `healthy_exchanges:2, coverage_percent:2.0, public_live_proof_ok:true, live_data_truth_integrated:true`. `compute_universe_coverage` → `live_ingestion_sources:2, ingestion_health_rows:0`. On-demand probe, not scheduled ingestion. |
| 10 | **Hard-coded `VERIFIED_COMPLETE` in gate-cert** | **ABSENT** | `run_all_gates()` → `passed:true, hardcoded_verified_complete_present:false`; zero `VERIFIED_COMPLETE` values in gate output. Classifier helper can *derive* the string from evidence; it does not hard-assign it. |
| 11 | **Super Terminal synthetic ≈100 leftovers** | **STILL PRESENT IN SOURCE** | At `3981914`, `super_terminal.py` contains `synthetic_fallback` and hard-coded books `[[100.0, 20.0], …]` plus microstructure sample `[[100.0, 5.0], …]`. Runtime this probe hit live OKX anchor, but the synthetic path remains reachable. Does **not** consume `canonical_truth_bus`. |
| 12 | **`product_complete` census** | **40 True / 30 False** | Unchanged True-heavy periphery (`institutional_assurance` ×13, heroes, org_*, oidc, commerce, etc.). New depth modules correctly False. |

Net: depth modules added since `2af4e5f` are **real and behaviorally observable**, but every path that would be required for COMPLETE still fails a strict live-authority test (reconstructed depth, paper fill, SQLite-not-HA, synthetic ST fallback, Jupiter blocked).

---

## DEFECTS FOUND (this SHA)

### CRITICAL

1. **No live venue FILL; paper lifecycle is being used as stand-in for execution truth.**
   `venue_fill_proof` with default env → `live_fill:false, mode:paper_lifecycle, dry_run:true`.
   OMS `submit_to_venue(dry_run=True)` then manually `transition(..., FILL)` / reconcile.
   Jupiter live submit remains `NOT_IMPLEMENTED` / `executed:false`.
   No repository path produced a venue-acknowledged live/testnet FILL at this SHA.
   Blocks COMPLETE.

2. **Canonical "live books" are live *prices* with fabricated depth sizes — consumers treat them as real L2.**
   `canonical_truth_bus.refresh_live_truth` builds books as
   `bids: [[bid*(1-0.0001*i), 2.0+i] …]` (and Kraken `1.5+i`) around public top-of-book —
   not exchanged depth. `decision_e2e` and whale readiness then compute exitability / risk depth
   on those invented quantities (`whale_ready:true`, risk `executable:true` observed).
   Live→canonical wiring is real; **depth authority is still synthetic**. Blocks VERIFIED_COMPLETE
   for whale/risk/decision.

### HIGH

3. **Production consumers are not uniformly bus-gated; synthetic ≈100 fallbacks remain.**
   `risk_intelligence` and `decision_intelligence_engine` never call the bus.
   `super_terminal._derivatives_pack` bypasses the bus, keeps `synthetic_fallback` hard-coded
   books at ≈100.0, and fabricates perpetual legs / funding rates even on the "live" path.
   `whale_execution_evidence` defaults `require_live=False` and may self-label
   `product_complete:true` when the 50k gate passes on reconstructed books.

4. **Institutional "DB authority" is SQLite dual-write, not production HA authority.**
   Isolated probe proved dual-write + cold hydrate + audit events on SQLite.
   `ops_recovery` proves file-copy reopen of that SQLite DB only.
   No Postgres HA, no multi-process durability proof, no RPO/RTO exercise.
   JSON mirrors still exist; claiming DB authority without HA/DR is overstated.

### MEDIUM

5. **`product_complete:True` persists on 40 lines / ~22 peripheral modules** after the honesty sweep
   of the truth stack. Contradicts a strict 0-VERIFIED_COMPLETE institutional posture.

6. **Universe live proof remains on-demand with `ingestion_health_rows:0`.**
   Coverage `2.0%` / `healthy_exchanges:2` is a query-time probe, not scheduled ingestion.

7. **B2B inbox "delivered" is durable-but-detached** from the product `in_app_alerts` store
   (writes `alert_deliveries.jsonl` only; no `in_app_alerts` reference in `b2b_institutional_ops`).

8. **Gate-cert `passed:true` remains a self-probe** — honest about no hard-coded
   `VERIFIED_COMPLETE`, but still not independent evidence of live execution completeness.

### LOW

9. **Truth-bus / ST perpetual legs and funding rates are derived/hard-coded constants**
   (`funding_rate: 0.0001 / -0.00005`), not venue futures/funding feeds.

10. **Primary workspace HEAD moved during audit** to `3c01c26` (post-SHA remediation attempt).
    Evidence above is pinned via detached worktree; future auditors must re-pin.

---

## DOMAIN STATUSES & SCORES (/100 — adversarial, no target)

| # | Capability / Domain | Classification | Score | Evidence |
|---|---|---|---:|---|
| 1 | Canonical Data / Truth Bus | PARTIAL | 66 | Live TOB→bus→cache works; depth sizes fabricated; fail-closed on empty |
| 2 | Streaming / Universe coverage | PARTIAL | 52 | healthy 2 / coverage 2.0%; `ingestion_health_rows:0`; on-demand |
| 3 | live_data_truth_probe | PARTIAL | 68 | 2 live venues, stale_as_live:0, integrated into health |
| 4 | Financial Truth | PARTIAL | 62 | fee_matrix fail-closed (unchanged posture) |
| 5 | Execution Truth | PARTIAL | 48 | Paper fill lifecycle proved; **live_fill:false**; Jupiter blocked |
| 6 | Cross-Exchange Arb | PARTIAL | 56 | Math present; books injected / reconstructed |
| 7 | Triangular Arb | PARTIAL | 50 | Present; not live-fed end-to-end |
| 8 | Spot-Futures Arb | PARTIAL | 54 | ST computes on live-anchored spot + **derived** perp, else ≈100 fallback |
| 9 | Funding Arb | PARTIAL | 52 | Uses hard-coded funding constants |
| 10 | CEX-DEX | PARTIAL | 56 | fees_known gate; Jupiter submit NOT_IMPLEMENTED |
| 11 | OMS (+ DB dual-write) | PARTIAL | 70 | Reconcile mismatch + SQLite dual-write + hydrate + idempotency isolation — still dry-run |
| 12 | Full Risk | PARTIAL | 58 | Domains compute when depths passed; module does not pull bus |
| 13 | Correlation/Contagion | PARTIAL | 60 | Blocking gate real when invoked |
| 14 | Decision brain / E2E | PARTIAL | 62 | E2E object LIVE→…→LEARNING exists; hermetic calibration fixed; heuristic confidence; reconstructed books |
| 15 | Super Terminal derivatives | PARTIAL | 50 | Live OKX anchor path works; **≈100 synthetic leftovers remain**; no bus |
| 16 | Whale | PARTIAL | 58 | Depth-walk real; default `require_live=False`; ready on reconstructed sizes |
| 17 | Portfolio | PARTIAL | 58 | Analyzer + fill-proof portfolio upsert on paper path |
| 18 | B2B alert delivery | PARTIAL | 60 | inbox delivered; pager/email/slack pending_connector; webhook fail-closed |
| 19 | Enterprise Identity | PARTIAL | 62 | Modules load; JSON store; some `product_complete:true` remain |
| 20 | White Label | SCAFFOLD | 36 | JSON tenant branding; `product_complete:false` |
| 21 | Jupiter Live Submit | NOT_IMPLEMENTED | 32 | Always non-executing fail-closed |
| 22 | Soft-Launch Separation | PARTIAL | 60 | Config-gated (unchanged posture) |
| 23 | Transferability / Ops recovery | PARTIAL | 52 | SQLite backup/restore probe ok; no live DR |
| 24 | Reliability / Observability | PARTIAL | 50 | Fail-closed paths; suite sample green on hermetic test; HA/DR inactive |
| — | Gate-Cert Evidence Layer | PARTIAL | 56 | No hard-coded VERIFIED_COMPLETE; self-probe |

---

## SCORES SUMMARY

| Track | Score |
|---|---:|
| Data & Streaming truth (1-3) | 62 |
| Financial & Execution (4-10) | 55 |
| Risk / OMS (11-13) | 63 |
| Decision brain (14) | 62 |
| Product / Institutional (15-21) | 52 |
| Security & separation (19,22) | 61 |
| Ops / Reliability (23-24) | 51 |
| Honesty of completion evidence | 64 |

### OVERALL: **70 / 100**

(Prior clean-room `2af4e5f` = 64. The **+6** reflects behaviorally verified depth from `aa57acc`+`9e29083`+`3981914`:
canonical truth bus actually delivers live TOB into `get_live_books`; decision E2E builds a full
LIVE→…→LEARNING object; OMS SQLite dual-write/hydrate/idempotency isolation works; paper fill
lifecycle + ops SQLite backup probe exist; decision calibration is hermetic again.
The gain is **hard-capped** because bus depth sizes are fabricated, Super Terminal still carries
≈100 synthetic leftovers, fills remain paper-only, and DB authority is SQLite — not live venue
execution or Postgres HA.)

---

## FINAL VERDICT

# NOT COMPLETE

**Reason.** At SHA `3981914b1b4604d739b06e1b4a7ad05124571728`, BLACKDARK added real institutional-depth
scaffolding that **does** move live public top-of-book into a canonical bus and through a decision E2E
object, and OMS can dual-write/reconcile against SQLite with cold-mirror hydrate. Completeness is
nonetheless **disproved**:

- **VERIFIED_COMPLETE count = 0** across the mandatory focus set.
- **Critical:** no live/testnet venue FILL (`live_fill:false`); bus books use **fabricated depth sizes**.
- **High:** ST/risk/decision are not uniformly bus-gated; ≈100 synthetic fallbacks remain; SQLite ≠ HA.
- Jupiter live submit remains **NOT_IMPLEMENTED**; universe ingestion rows remain **0**.

Per the rule — COMPLETE only if repository-controlled mandatory capabilities are truly
VERIFIED_COMPLETE with behavioral live-input evidence and no open Critical/High repo defects —
the verdict is decisive.

---

## PROBE METHODOLOGY (this SHA)

- Audited via detached worktree at `3981914` after primary HEAD drift to `3c01c26` (documented above).
- `canonical_truth_bus.refresh_live_truth_sync` + `get_live_books(require_live=True)`.
- Consumer import/source inspection + runtime samples (`whale`, `build_super_terminal`, `decision_e2e`).
- `venue_fill_proof.prove_fill_lifecycle` (default env).
- Isolated `config.DB_PATH` + `oms._PATH/_DATA_BASE` dual-write / hydrate / mismatch reconcile.
- `ops_recovery.prove_sqlite_backup_restore`.
- B2B `orchestrate_alert` for inbox/pager/email/slack/webhook with connector env cleared.
- `jupiter_dex_adapter.execute_swap(dry_run=False)` + `adapter_status`.
- `prove_multi_venue_live` / awaited `live_rollout_status` / `compute_universe_coverage`.
- `institutional_gate_cert.run_all_gates` hardcoded-VERIFIED_COMPLETE check.
- `product_complete` True/False census via `git grep` on `3981914` `*.py` excluding tests/docs.
- Spot pytest: `test_decision_intelligence_engine_stand_down` **passed**;
  `tests/test_institutional_depth_completion.py` **7 passed** (tests ≠ completeness evidence).

*End of clean-room audit for candidate SHA `3981914b1b4604d739b06e1b4a7ad05124571728`.*
