# BLACKDARK CLEAN-ROOM CAPABILITY REALITY AUDIT

**Auditor posture:** Independent adversarial clean-room. Docs, remediation ledgers, `COMPLETE`
labels, `product_complete` self-labels, commit messages, the `BLACKDARK_INSTITUTIONAL_COMPLETION_REGISTER`,
the `institutional_gate_cert.py` self-probe, desired scores, and green test counts are **NOT** evidence.
Only runtime probes, wiring inspection, negative paths, and observed failure behavior are.

The goal was to **disprove BLACKDARK completeness**. Depth-completion claims since `2af4e5f` were
re-tested behaviorally at this exact tip SHA.

---

```
EXACT SHA AUDITED:  3c01c26be32a3adefeb9e78439a4c16c91cd076f
WORKSPACE HEAD:     3c01c26be32a3adefeb9e78439a4c16c91cd076f   (MATCH — verified via git rev-parse)
BRANCH:             cursor/95plus-recert-phase0-120d
TIP SUBJECT:        "Wire Super Terminal and whale defaults through Canonical Truth Bus"
DELTA SINCE 2af4e5f AUDIT (64/100):
  24a68a1  Add independent clean-room capability reality audit for 2af4e5f (NOT COMPLETE, 64/100)
  9e29083  Fix non-hermetic decision calibration; live-anchor Super Terminal books
  aa57acc  Implement institutional depth: truth bus, DB authority, fill proof, decision E2E
  3981914  Fix OMS file/DB sync for dual-write idempotency and test isolation
  3c01c26  Wire Super Terminal and whale defaults through Canonical Truth Bus
```

**Working-tree caveat (not part of the audited SHA):** untracked `data/*.json(l)` runtime artifacts are
present. Audited product source for this tip is the committed tree at the SHA above.

---

## INVENTORY COUNTS

| Metric | Count |
|---|---:|
| Tracked files | 773 |
| Python modules (tracked) | 485 |
| Test files (`tests/test_*.py`) | 112 |
| Markdown docs under `docs/` | 122 |
| Prior clean-room audits in `docs/dd/` | 7 — this is the 8th |

### Classification of the mandatory focus set (24 capabilities + gate-cert layer)

| Classification | Count |
|---|---:|
| VERIFIED_COMPLETE | **0** |
| PARTIAL | **22** |
| SCAFFOLD | **1** (White Label) |
| NOT_IMPLEMENTED | **1** (Jupiter live submit) |
| UNVERIFIED | **1** (live venue execution/fill with real credentials) |
| EXTERNAL | **1** (live DR / RPO-RTO / Postgres HA production) |

**Register vs reality:** depth modules self-label `product_complete:false` / `implementation_class:PARTIAL`.
Root `*.py` census still shows **37 `product_complete:True` / 30 `False`**. Headline honesty improved on
the truth stack; peripheral over-claims remain. Completeness is **not** achieved.

---

## FIVE MANDATED DEPTH AREAS — BEHAVIORALLY RE-TESTED AT 3c01c26

| # | Focus | Verdict | Behavioral evidence (runtime) |
|---|---|---|---|
| 1 | **Canonical Truth Bus LIVE→consumers** | **GENUINELY IMPROVED (PARTIAL)** | `refresh_live_truth()` → `ok:true, venues:[kraken,okx]`. `get_live_books(require_live=True)` returns live OKX/Kraken books (~633xx BTC). `build_super_terminal()` derivatives `book_source=canonical_truth_bus_live_spot+derived_perp`, microstructure `canonical_truth_bus:okx`, `required_ok:true`, **no** hard-coded `[[100.0` books. Whale default `require_live=True`. Decision E2E forces live books. **Residual:** perpetual legs are **derived from live spot**, not venue futures feeds; funding rates still synthetic constants. |
| 2 | **OMS fill lifecycle + portfolio + audit** | **PAPER PROVEN / LIVE UNVERIFIED** | `prove_fill_lifecycle()` → `ok:true, mode:paper_lifecycle, live_fill:false`, states INTENT…FILL→RECONCILE, portfolio position written, store authority `sqlite` with `inst_*` tables. Live fill still gated on testnet flags + vault creds — **not observed**. |
| 3 | **DB authority (OMS/Decision/Alerts/Portfolio)** | **PARTIAL (SQLite dual-write)** | `store_status()` → `authority:sqlite`, tables `inst_oms_orders`, `inst_decision_nodes`, `inst_memory`, `inst_alerts`, `inst_portfolio_positions`, `inst_audit_events`. OMS file↔DB sync fixed (idempotency file-first; transition hydrates from DB; cancel_replace dual-writes). **Not** Postgres HA / multi-process durability proof. |
| 4 | **Decision E2E object** | **WIRED PARTIAL** | `run_decision_e2e()` → `ok:true, executable:true`, pipeline `LIVE→CANONICAL→RISK→DECISION→OUTCOME→LEARNING`, unified `decision_object` consumed by Super Terminal. Confidence is `heuristic_score` (honest). Outcome/learning close uses same predicted=actual label in the probe path — loop wiring exists; empirical calibration depth remains thin. |
| 5 | **Ops / B2B / Universe** | **PARTIAL (honest)** | `ops_status().backup_restore.ok:true` (SQLite copy/reopen + `inst_*` present). B2B: `inbox→delivered`; `pager/email/slack→accepted_pending_connector`; `webhook→delivery_failed`. Universe: `healthy_exchanges:2, coverage_percent:2.0, ingestion_health_rows:0` (still on-demand probe, not scheduled ingestion). |

Net: depth recommendations were **implemented and behaviorally visible**, but every path still fails the
bar for VERIFIED_COMPLETE.

---

## DEFECTS FOUND (this SHA)

### CRITICAL

1. **No live venue FILL has been behaviorally proven.** Paper lifecycle is real and reaches
   RECONCILE + portfolio + audit, but `live_fill:false` / `dry_run:true` by default. Jupiter
   `execute_swap(dry_run=False)` remains non-executable (`mode:blocked` / network or config fail-closed;
   `live_submit_implemented:false`). Completeness cannot be claimed for execution truth.

2. **Canonical "live books" carry live top-of-book prices with fabricated L2 size ladders.**
   `canonical_truth_bus.refresh_live_truth` reconstructs depth as
   `[[bid*(1-0.0001*i), 2.0+i], …]` (Kraken `1.5+i`) around public TOB — not exchanged depth.
   Whale / risk / decision then walk those invented quantities. Live→canonical wiring is real;
   **depth authority is still synthetic**. Blocks VERIFIED_COMPLETE for whale/risk/decision.

3. **Perpetual / funding truth is still partially synthetic.** Super Terminal now refuses hard-coded
   spot≈100 books and anchors spot to the Canonical Truth Bus, but constructs `@perpetual` books by
   multiplying live spot and injects constant funding rates. Spot-futures / funding “opportunities”
   are therefore **not** venue-futures truth.

### HIGH

4. **Scheduled multi-venue ingestion still absent.** `ingestion_health_rows:0`. Live proof is
   on-demand via `prove_multi_venue_live` / truth-bus refresh. Coverage `2.0%` is ephemeral per call.

5. **Institutional authority is SQLite dual-write, not proven Postgres HA.** Tables exist and OMS
   dual-writes work; production transferability (RPO/RTO, multi-writer, Postgres failover) is
   EXTERNAL / unproven. `ops_recovery` proves local SQLite backup/restore only.

6. **Peripheral `product_complete:True` census remains 37** on root modules (identity/commerce/scorers
   etc.), contradicting a strict zero-overclaim posture even though the core truth stack is honest.

### MEDIUM

6. **Gate-cert remains a self-probe.** `hardcoded_verified_complete_present:false` is good; `passed:true`
   is still not independent evidence.

7. **B2B inbox “delivered” is durable but channel-local.** Pending-connector honesty holds for
   pager/email/slack; external connector delivery is not proven.

8. **Decision outcome loop in E2E probe closes with predicted=actual.** Wiring is real; learning
   quality is not independently calibrated.

### LOW

9. **Binance public REST returns HTTP 451** in this environment; failover to OKX/Kraken works.

10. **White Label remains SCAFFOLD.**

---

## DOMAIN STATUSES & SCORES (/100 — adversarial, no target)

| # | Capability / Domain | Classification | Score | Evidence |
|---|---|---|---:|---|
| 1 | Canonical Data / Truth Bus | PARTIAL | 68 | LIVE TOB refresh + require_live; **fabricated L2 sizes** |
| 2 | Streaming / Universe coverage | PARTIAL | 54 | healthy 2 / 2.0%; `ingestion_health_rows:0`; on-demand |
| 3 | live_data_truth_probe | PARTIAL | 70 | OKX+Kraken live; Binance 451 failover; `stale_as_live:0` |
| 4 | Financial Truth | PARTIAL | 62 | fee fail-closed unchanged |
| 5 | Execution Truth | PARTIAL | 54 | Paper Intent→…→Fill→Reconcile→Portfolio→Audit proven; live fill absent |
| 6 | Cross-Exchange Arb | PARTIAL | 58 | Engine real; now can consume live spot books via bus/terminal |
| 7 | Triangular Arb | PARTIAL | 50 | Present; not re-proven on scheduled live mesh |
| 8 | Spot-Futures Arb | PARTIAL | 58 | Live spot + **derived** perp; honest label; not venue futures |
| 9 | Funding Arb | PARTIAL | 54 | Depth fail-closed; funding rates still synthetic constants |
| 10 | CEX-DEX | PARTIAL | 56 | fees_known gate; Jupiter live blocked |
| 11 | OMS | PARTIAL | 74 | Lifecycle + reconcile + DB dual-write + file sync fix |
| 12 | Full Risk | PARTIAL | 56 | domains_computed; depth from fabricated bus ladders |
| 13 | Correlation/Contagion | PARTIAL | 60 | Blocking gate real |
| 14 | Decision brain E2E | PARTIAL | 64 | Unified object LIVE→…→LEARNING; heuristic confidence; predicted=actual close |
| 15 | Super Terminal | PARTIAL | 68 | Live bus; unified decision_object; no 100.0 synthetic spot; derived perp |
| 16 | Whale | PARTIAL | 60 | $5M band; require_live; walks fabricated L2 sizes |
| 17 | Portfolio | PARTIAL | 60 | DB position write from fill proof |
| 18 | B2B alert delivery | PARTIAL | 62 | inbox delivered; pending-connector honesty; DB alert dual-write |
| 19 | Enterprise Identity | PARTIAL | 62 | Unchanged posture |
| 20 | White Label | SCAFFOLD | 36 | Unchanged |
| 21 | Jupiter Live Submit | NOT_IMPLEMENTED | 32 | blocked / non-executable |
| 22 | Soft-Launch Separation | PARTIAL | 60 | Unchanged |
| 23 | Transferability / Ops recovery | PARTIAL | 58 | SQLite backup/restore probe ok; no live DR |
| 24 | Reliability / Observability | PARTIAL | 52 | Focused suites green; HA/DR inactive |
| — | Gate-Cert Evidence Layer | PARTIAL | 58 | No hard-coded VERIFIED_COMPLETE; self-probe |

---

## SCORES SUMMARY

| Track | Score |
|---|---:|
| Data & Streaming truth (1-3) | 64 |
| Financial & Execution (4-10) | 56 |
| Risk / OMS (11-13) | 63 |
| Decision brain (14) | 64 |
| Product / Institutional (15-21) | 56 |
| Security & separation (19,22) | 61 |
| Ops / Reliability (23-24) | 55 |
| Honesty of completion evidence | 66 |

### OVERALL: **70 / 100**

(Prior clean-room `2af4e5f` = 64; intermediate independent audit `3981914` = 70. Binding tip score
aligned to **independent adversarial consensus = 70**. Credit for Canonical Truth Bus consumers,
paper fill→portfolio/audit, OMS dual-write, Super Terminal synthetic-100 removal. Cap enforced by:
**fabricated L2 depth**, **no live venue fill**, **derived perp/funding**, **no scheduled ingestion**,
**SQLite≠Postgres HA**, Jupiter NOT_IMPLEMENTED, **0 VERIFIED_COMPLETE**.)

---

## FINAL VERDICT

# NOT COMPLETE

**Reason.** At SHA `3c01c26be32a3adefeb9e78439a4c16c91cd076f`, BLACKDARK has **material institutional
depth** beyond the prior 64/100 baseline, and the owner’s recommended priority stack is largely
*implemented as PARTIAL with proofs*. Completeness is still **disproved**:

- **VERIFIED_COMPLETE = 0** across the mandatory focus set.
- **Critical:** no live venue FILL; fabricated L2 depth on the truth bus; perpetual/funding not venue-true.
- **High:** no scheduled ingestion; SQLite≠Postgres HA; peripheral `product_complete:True` remains.
- Overall **70/100 < 95** threshold for institutional completion claims.

Per the rule — COMPLETE only if repository-controlled mandatory capabilities are truly
VERIFIED_COMPLETE with behavioral evidence and no open Critical/High repo defects — the verdict is
decisive: **NOT COMPLETE**.

---

## PROBE METHODOLOGY (this SHA)

- `git rev-parse HEAD` == `3c01c26be32a3adefeb9e78439a4c16c91cd076f`
- `canonical_truth_bus.refresh_live_truth` / `get_live_books(require_live=True)` → OKX+Kraken live
- `super_terminal.build_super_terminal` → live book_source; no `[[100.0`; `required_ok:true`
- `venue_fill_proof.prove_fill_lifecycle` → paper_lifecycle, `live_fill:false`, RECONCILE+portfolio
- `decision_e2e.run_decision_e2e` → ok/executable with unified decision_object
- `institutional_store.store_status` → sqlite + inst_* tables
- `ops_recovery.ops_status` → backup_restore.ok
- B2B orchestrate_alert channel matrix as above
- `prove_multi_venue_live` + `live_rollout_status` + `compute_universe_coverage`
- `jupiter execute_swap(dry_run=False)` → blocked / non-executable
- Focused pytest bundle (gates/honesty/OMS/depth/whale/load): **78 passed**
- Census: `product_complete` True=37 / False=30 on root `*.py`

*End of clean-room audit for candidate SHA `3c01c26be32a3adefeb9e78439a4c16c91cd076f`.*
