# BLACKDARK — Data / Storage / Compounding Governing Reference

**Status:** ACTIVE — review & acceptance baseline only (NOT a literal build backlog)  
**Adopted:** 2026-08-21  
**User directive:** Save, register, govern — do not reprioritize or open branch/PR because of this doc alone.  
**Pairs with:** `INSTITUTIONAL_GOVERNING_REFERENCE.md`

---

## Canonical document

| Field | Value |
|---|---|
| Title | Master Compounding Value, Platform & Pre-Launch Asset Specification |
| Arabic | وثيقة تجميع تخزين البيانات - البلاتفورم - تسريع التخزين |
| Role | Governing reference for data, storage, knowledge compounding, platform boundaries, pre-launch accumulation |
| Integrity | Five-pass review PASS (ingestion, structure, preservation, consultant rewrite, reverse trace + render QA) |
| **Archived PDF** | `/cursor/stores/self/BLACKDARK_DATA_STORAGE_COMPOUNDING_MASTER_SPEC.pdf` |
| Upload copy | `/home/ubuntu/.cursor/projects/workspace/uploads/___________________________-____________-_______________2700.pdf` |
| Extracted text (agent) | `/tmp/data_platform_spec.txt` (regenerate: `pdftotext …/BLACKDARK_DATA_STORAGE_COMPOUNDING_MASTER_SPEC.pdf /tmp/data_platform_spec.txt`) |

---

## How to use this reference

| DO | DO NOT |
|---|---|
| Classify repo state: **applied / partial / missing / not needed now** | Create 12 separate Vault DBs |
| Review decisions via Source→Evidence chain | Rebuild what already works (tiered storage, lake, registries) |
| Enforce evidence-class separation on every artifact | Mix BACKTESTED/SHADOW/PRODUCTION in metrics or marketing |
| Extend partial modules in place | Treat doc as sprint backlog |
| Map logical 12 Vaults → existing modules | Duplicate registries (Truth/Claims/etc.) without gap proof |

**Closure gate (reference):** GATE — PROPRIETARY ASSET ACCUMULATION & DATA FLYWHEEL READINESS → `VERIFIED COMPLETE` or `NOT READY`.

---

## Core principle

> **DON'T DELETE KNOWLEDGE — COMPOUND IT.**  
> Structured · versioned · searchable · attributable · governed.

**Dependency chain (review order):**

```
Source Data → Normalize/Lake/Hot tiers → Feature → Engine → Signal
→ Prediction/Decision → Version → Outcome → Error → Learning → Evidence
```

---

## Evidence classes — THE HEART OF THE SPEC

Four classes are **mandatory** and must never be conflated in metrics, UI, or DD packs.

| Class | Spec meaning | Code reality (2026-08-21) | Verdict |
|---|---|---|---|
| **BACKTESTED** | Point-in-time replay on history; no future leakage | `ml/market_replay_bootstrap.py` (`SOURCE=market_replay_v1`); `scripts/seed_oracle_history.py` (`source=historical_seed`, excluded from live metrics); warm Parquet tier noted for backtests in `storage_tier_manager.py`; `contradiction_replay.py` | **Applied** (implicit via `source` tags, not unified enum) |
| **SIMULATED** | Synthetic/stress; must stay labeled | `trade_simulator.py` (paper); `onchain_tracker.py` (`source=simulated`); `dex_fetcher`/`perp_dex_fetcher` synthetic books; `jupiter_dex_adapter` synthetic economics; `scripts/train_rl_policy.py` synthetic samples; regime bootstrap flags in `d5_regime_honesty.py` | **Partial** — labeled in places, no global `evidence_class=SIMULATED` |
| **SHADOW-LIVE FORWARD** | Live timestamped prediction/decision before outcome; no money | Live `oracle_predictions` (`source` default `oracle` / `arb_unified_v1`) + `oracle_track_record` hash chain on create/resolve; `locked_predictions.py` sealed forward; `signal_registry.py` append | **Partial** — behavior exists; no explicit SHADOW class field |
| **PRODUCTION VERIFIED** | Real post-launch usage after go-live | `data_moat_guard.py` production gates; live-only SQL in `oracle_integrity.py` / `sql_safety.py`; production E2E matrix still NO-GO (open PR context) | **Partial / NOT VERIFIED** for full platform |

### Separation guards already in code (keep — do not rebuild)

| Mechanism | File | Effect |
|---|---|---|
| Synthetic source filter | `oracle_integrity.py` | `historical_seed` excluded from live metrics |
| Live-only SQL | `sql_safety.py`, `oracle_integrity.live_source_sql()` | Training/public stats exclude seed |
| Production moat guard | `data_moat_guard.py` | Blocks synthetic seed in prod; requires `features_json` for live oracle |
| Public accuracy split | `ml/public_accuracy.py`, `oracle_track_record.public_track_record()` | Live vs `synthetic_demo_data` blocks |
| Honest seed script | `scripts/seed_oracle_history.py` | Tags + excludes from training/metrics |
| Replay bootstrap honesty | `ml/market_replay_bootstrap.py` | Point-in-time features; `market_replay_v1` tag |
| CSO priority | `cso_priority_chain.py` | Forbids synthetic as proprietary AI moat |

### Gap (partial — do not duplicate; extend when tasked)

- No single **`evidence_class`** column/enum across all stores (predictions, signals, trades, events).
- **SHADOW-LIVE FORWARD** not named explicitly in schema — inferred from live oracle + unresolved state.
- **PRODUCTION VERIFIED** not stamped per artifact — inferred from env + E2E (still open).
- Some modules use `simulated`/`synthetic`/`paper` inconsistently — review on touch, unify labels only if needed.

**Review rule:** When adding/changing data paths, assign one of the four classes explicitly in metadata; never promote BACKTESTED → PRODUCTION without new evidence.

---

## 12 logical Vaults → repo mapping (NO separate DBs)

| Vault | Applied | Partial | Missing | Primary anchors |
|---|---|---|---|---|
| **Data** | ✅ | | | `hot_storage.py`, `storage_tier_manager.py`, `data_lake.py`, `ingestion_snapshots`, `data_sources_registry.py` |
| **Intelligence** | ✅ | | | `signal_registry.py`, `data_provenance_score.py`, lake bundles |
| **Decision & Outcome** | | ⚠️ | | `oracle_track_record.py`, `database.oracle_predictions`, `decision_certificate.py` — no unified decision ledger |
| **Model** | | ⚠️ | | `ml/*`, `ml/drift_monitor.py`, `data/models/` — no formal experiment registry |
| **Failure** | | ⚠️ | | `kill_rate_board.py`, vetoes in `constitution_gates` — no Failure Corpus registry |
| **Evidence** | | ⚠️ | | `acquirer_evidence_pack.py`, `oracle_audit_chain`, `locked_predictions.py` — on-demand, not live auto Evidence Room |
| **IP** | | ⚠️ | | `signal_registry` lexicon, `corpus_passport.py` — no IP Provenance registry |
| **Product** | ✅ | | | `bd_platform/registry.py` (40-feature matrix) |
| **Customer** | | ⚠️ | | `database` users/billing — no compounding analytics store |
| **Distribution** | | | ❌ | No distribution knowledge graph |
| **Institutional** | | ⚠️ | | `institutional_assurance.py`, `enterprise_sso.py` partial |
| **Corporate/DD** | | ⚠️ | | `docs/*`, evidence packs — not auto-updating DD vault |

**Engineering judgment:** Tiered storage + domain modules **already implement** the 12-vault *intent*. Do not create 12 databases.

---

## 8 compounding engines

| Engine | Status | Evidence |
|---|---|---|
| DATA COMPOUNDING | **Applied** | Hot/warm/cold tiers, lake, 100+ sources registry |
| INTELLIGENCE COMPOUNDING | **Applied** | Signal registry, derived metrics, provenance score |
| LEARNING COMPOUNDING | **Partial** | Oracle outcomes + labeling; replay bootstrap; weak event library |
| TECHNOLOGY COMPOUNDING | **Partial** | ML artifacts + drift envelope; no experiment genealogy |
| TRUST COMPOUNDING | **Partial** | Audit chain, locked predictions, evidence pack; PRODUCTION VERIFIED open |
| PRODUCT & CUSTOMER | **Partial** | UX modes, billing hooks; weak time-to-value instrumentation |
| DISTRIBUTION | **Missing** | Pre-launch SEO/viral compounding not built |
| CORPORATE VALUE | **Partial** | Corpus passport, acquirer pack, DD docs |

---

## Minimum Pre-Launch Accumulation Core (12)

| # | Item | Status | Repo anchor | Evidence class notes |
|---|---|---|---|---|
| 1 | Live Shadow Collection | **Partial** | `binance_ws_ingest`, `ingestion_scheduler`, hot pipeline | Live ingest ≠ shadow on all engines |
| 2 | Historical Backfill | **Partial** | `seed_oracle_history`, replay bootstrap, warm Parquet | BACKTESTED / historical_seed |
| 3 | Signal Registry | **Applied** | `signal_registry.py` | Links signal→prediction; provenance in row |
| 4 | Prediction Ledger | **Applied** | `oracle_predictions` + `oracle_track_record` + audit chain | SHADOW-forward when live unresolved |
| 5 | Decision Ledger | **Partial** | `decision_certificate.py`, scattered DB | No Decision→Exposure→Outcome table |
| 6 | Automated Outcome Evaluator | **Applied** | `resolve_oracle_prediction`, `ml/public_accuracy.py` | Live-only metrics |
| 7 | Data Provenance | **Applied** | `data_provenance_score.py`, freshness guards | Decision-grade bands |
| 8 | Algorithm/Model Versioning | **Partial** | `data/models/`, drift files | No model/experiment registry |
| 9 | Historical Replay Engine | **Partial** | `market_replay_bootstrap`, `contradiction_replay` | BACKTESTED |
| 10 | Market Event Library | **Missing** | — | No dedicated event KB store |
| 11 | Failure Registry | **Partial** | `kill_rate_board`, kill events in signal registry | No unified failure corpus |
| 12 | Evidence Store | **Partial** | `acquirer_evidence_pack.py` | Aggregator only; not live auto-updating |

**Flywheel gate verdict:** `NOT READY` as institutionally complete — **foundation is sound; extend partials, do not rebuild applied layers.**

---

## Platform architecture (design mandates)

| Mandate | Status | Notes |
|---|---|---|
| Platform not website-only | **Partial** | API/B2B/GraphQL exist; intelligence still coupled to dashboard in places |
| Multi-tenant / RBAC / audit | **Partial** | Auth/MFA progress; full tenant isolation incomplete |
| Entitlement engine | **Missing** | Tier logic scattered in config/code |
| Intelligence core ≠ HTML | **Partial** | `data_lake` read pattern is correct pattern |
| Event-driven architecture | **Partial** | WS ingest + schedulers; not full event bus for all domains |
| Data Rights Registry | **Missing** | `data_sources_registry` has specs, not rights/retention/training fields |
| Vendor independence | **Partial** | Hot storage backends abstracted (NDJSON/ClickHouse/Timescale) |
| Exit/acquisition packaging | **Partial** | `acquirer_evidence_pack`, `corpus_passport` |

---

## Not needed now (per spec + repo reality)

- 12 physical Vault databases or parallel registries (Truth/Claims/Capability) without proven gap
- Full Financial Knowledge Graph at scale before shadow engines stable
- Distribution compounding infrastructure pre-launch
- Collect-all-data without purpose/rights (`data_moat_guard` already guards against fake moat)
- Re-implementing tiered storage or signal registry

---

## Review checklist (invoke on data/storage tasks)

1. Which vault / pre-launch core item (if any)?
2. **Applied / partial / missing** — what exists in code?
3. **Evidence class** for every new/changed artifact?
4. Does change **compound** existing stores or **duplicate**?
5. Institutional baseline control (DAT/QA/AI/FIN) satisfied?
6. No BACKTESTED/SIMULATED promoted to PRODUCTION metrics?

---

*Update this file only on explicit user instruction or when assigned work materially changes classification.*
