# Batch04 Phase-1 Delivery — IDs 151–200

**Date:** 2026-09-03  
**Scope:** Official Batch04 only (`official_batch=batch04`, IDs 151–200)  
**Phase:** §4 pre-build delivery — **no closure declared**  
**Branch:** `cursor/batch-04-151-200-e85e`

---

## Executive summary

| Metric | Value |
|--------|------:|
| IDs in scope | 50 (151–200) |
| `batch04_independent` | **0** (no PRODUCTION-ALIGNED in scope yet) |
| `progress_826` | **148** (unchanged — batch04 not counted) |
| Batch05 (201+) | **BLOCKED** — owner approval required |
| Live validation | **AWAITING_DEPLOY** per owner agreement |
| Sonar QG PR #362 | PASSED on `new_coverage=100%` (batch03 branch; separate from batch04 work) |

---

## 1) RTM inventory (`docs/BATCH04_RTM_151_200.json`)

50 rows — each with: `official_batch=batch04`, `status`, `prebuild_classification`, `binding_file_planned`, `hero_underlying`, `duplicate_candidates`.

| RTM status | Count |
|------------|------:|
| PENDING | 21 |
| NOT_COMPLETE | 29 |
| PRODUCTION-ALIGNED | 0 |

| Pre-build class | Count | Meaning |
|-----------------|------:|---------|
| Brownfield | 50 | Hero/bd_platform or track-default code exists; **split-brain risk** — cannot promote without semantic realignment |
| Greenfield | 0 | No ID is truly code-free (all have hero evidence or track_default stubs) |
| Stub | 0 | Classified as Brownfield when track_default present |

**No `cap646/batch04_production.py` or `batch04_dedicated.py` exists.** Runtime routes 151–200 via generic track handlers except:
- **#175** → `LEGACY_BATCH01_EXTENSION_IDS` → `batch01` spine
- **#159** → `canonical_id` → **#103** (REUSED-LINK candidate)

---

## 2) Pre-Build Classification (`docs/BATCH04_PREBUILD_CLASSIFICATION_151_200.json`)

Per-ID: `prebuild_classification` + `build_decision` + `build_rationale`.

| Build decision (aggregate) | Count |
|----------------------------|------:|
| Strangler — realign hero / complete delegated | 48 |
| Canonical+Alias (REUSED) | 1 (#159) |
| Strangler — batch01 overlap (#175) | 1 |

**Strangler Fig default:** no Big Bang rewrite. Hero-layer functions (`bd_platform/*_layer.py`) reuse ID numbers with **different semantics** than official catalog for several IDs — mandatory realignment before PRODUCTION-ALIGNED.

---

## 3) Pre-acceptance draft (`docs/BATCH04_ACCEPTANCE_151_200.json`)

- `pre_probe: true`
- 50 rows × explicit `domain_rules[]` (includes `success` + `surface` as explicit rules)
- Generator: `scripts/generate_batch04_acceptance_151_200.py`
- Planned binding: `cap646/batch04_dedicated.py` → `_capNNN` (not yet implemented)

**Special acceptance rows:**

| ID | Status | Notes |
|----|--------|-------|
| 159 | REUSED-LINK | canonical #103 |
| 175 | OVERLAP-PARTIAL | batch01 spine — excluded from `batch04_independent` |
| 183 | REUSED-LINK candidate | hero reuse → #130 underlying |

---

## 4) Initial duplication scan (`docs/BATCH04_INITIAL_DUPLICATION_SCAN.json`)

Generator: `scripts/run_cap_dedup_audit_batch04.py`

### Confirmed / candidate pairs

| Pair | Scope | Classification |
|------|-------|----------------|
| 159 ↔ 103 | 151–200 vs 1–150 | DUPLICATE-CONFIRMED → REUSED-LINK |
| 175 ↔ batch01 | batch01 overlap | OVERLAP-PARTIAL |
| 183 ↔ 130 | hero layer | REUSED-LINK candidate |

### Internal clusters (OVERLAP-PARTIAL candidate — MECE audit required)

- **167–178** social sentiment/volume cluster
- **187–191** exchange flow cluster
- **194–200** onchain valuation metrics cluster
- **151, 152, 157, 163** research reporting cluster

### Scope searches

| Scope | Result |
|-------|--------|
| 151–200 internal | clusters + 3 confirmed/candidate pairs above |
| 151–200 vs 1–150 | confirmed pairs listed; full 50×150 matrix deferred to implementation |
| Hero batch scopes | `bd_platform/*_layer.py` searched — **split-brain documented** |
| Option-A SSOT (338,500,507,534) | NOT_APPLICABLE — no ID collision |

### jscpd (hero layer files — batch04 spine not yet created)

See `docs/BATCH04_INITIAL_DUPLICATION_SCAN.json` → `jscpd` section for clone counts on hero layer modules.

---

## 5) Confirmations

- **Batch05 (201+):** NOT opened — awaiting owner written approval after Phase-1 review
- **Live / Railway:** AWAITING_DEPLOY — no `LIVE_READY` claim
- **Batch03 non-regression:** mandatory on any future runtime/gateway/entitlement change (not triggered in this Phase-1 docs-only delivery)

---

## Next step (after owner review)

1. Owner approves Phase-1 RTM + acceptance + duplication scan
2. Implement `cap646/batch04_production.py` + `batch04_dedicated.py` + runtime wiring
3. Per-ID pentagonal closure with triple-match guard (mirror Batch03)
4. Re-run full MECE matrix after dedicated handlers exist

**Forbidden until owner approval:** declaring `LOCAL_GOVERNANCE_COMPLETE` for Batch04, opening Batch05, or claiming live 100% readiness.
