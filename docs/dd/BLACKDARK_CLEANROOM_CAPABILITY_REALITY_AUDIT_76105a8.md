# BLACKDARK CLEAN-ROOM CAPABILITY REALITY AUDIT

**Auditor posture:** Independent adversarial clean-room. Docs, remediation ledgers, `COMPLETE`
labels, `product_complete` self-labels, commit messages, the `BLACKDARK_INSTITUTIONAL_COMPLETION_REGISTER`,
`institutional_gate_cert.py` self-probe outputs, desired scores, and green test counts are **NOT**
evidence. Only runtime probes, wiring inspection, negative paths, and observed failure behavior are.

**Goal:** **DISPROVE** BLACKDARK completeness. Prefer NOT COMPLETE unless end-to-end live fill and
production-grade multi-AZ HA are behaviorally proven everywhere required.

---

```
REQUESTED TIP SHA:  76105a853f67fa5c72ccb7c61e0fad13ea48a7bc
WORKSPACE HEAD:     76105a853f67fa5c72ccb7c61e0fad13ea48a7bc   (MATCH)
BRANCH:             cursor/95plus-recert-phase0-120d
TIP SUBJECT:        "Expand mesh to 34 venues with regional symbols and thicken prove surfaces"
PRIOR BINDING:      94325d6 = 95/100 NOT COMPLETE, VERIFIED_COMPLETE 1
```

**Working-tree caveat:** dirty/untracked `data/*` runtime artifacts may be present. Audited product
source is the committed tip. **No product code was modified by this audit commit.**

---

## INVENTORY / CLASSIFICATION

| Classification | Count / note |
|---|---|
| VERIFIED_COMPLETE | **1** (`postgres_streaming_ha_rpo_rto` — local streaming; `cloud_multi_az=false`) |
| PARTIAL | truth bus, mesh/ingest, Jupiter quote+build+decode/sim, White Label, fill paper+book-walk, PG product-path |
| UNVERIFIED | live venue fill (no testnet creds) |
| LOCAL_EPHEMERAL_NOT_HA | dump/restore + product-path Postgres |
| Root `product_complete:True` literals | **0** |

---

## MANDATORY RUNTIME PROBES (this tip)

### Mesh / rollout / ingestion
| Field | Observed |
|---|---|
| `CORE_PUBLIC_CEX_MESH` size | **34** |
| `MESH_SYMBOL_OVERRIDES` | bitvavo EUR, bitflyer/coincheck/bitbank JPY, bithumb KRW, independentreserve AUD |
| `prove_multi_venue_live(full_mesh=True)` live/L2 | **34 / 34** |
| `canonical_mesh_adopted_count` | **32** (mesh L2 → canonical; OKX/Kraken adopt natively) |
| rollout | healthy **34** / target 100 → **34.0%** |
| durable ingest | live_sources **28**, coverage ~**46%**, pricing_logs **28** |
| Binance public | HTTP **451** |

### Jupiter
| Assertion | Observed |
|---|---|
| live quote | **true** |
| `/swap` build | **true** |
| VersionedTransaction decode | **true** |
| `simulateTransaction` (sigVerify=false) | **true** (HTTP 200; `AccountNotFound` expected for ephemeral) |
| `executed` / `broadcast` | **false** / **false** |
| submit `verified_complete` | **false** (no wallet) |

### Fill / WL / HA / PG
| Surface | Observed |
|---|---|
| fill `live_fill` | **false** (paper/protocol; venue `okx`) |
| book_walk | **ok**; impact_bps≈0.008; never claims live |
| White Label | PARTIAL; `builder_invoked=true`; real `build_super_terminal` brand path |
| HA streaming | **VERIFIED_COMPLETE**; RPO≈28ms RTO≈129ms; `cloud_multi_az=false` |
| PG product-path | ok, `authority=postgres`, LOCAL_EPHEMERAL_NOT_HA |

### Honesty
| Check | Observed |
|---|---|
| root `product_complete:True` | **0** |
| institutional depth tests | **35 passed** |

---

## Surface scores (0–100)

| Surface | Score | Notes |
|---|---:|---|
| Canonical Truth Bus | 97 | Light refresh + mesh canonical adoption |
| Decision → Intent → OMS | 95 | Unchanged E2E + dual-write |
| Venue FILL | 76 | Paper + L2 book-walk; still no live_fill |
| Jupiter DEX | 91 | Quote + build + decode + simulate; no signed broadcast |
| Postgres product path | 93 | Ephemeral OMS round-trip |
| Postgres streaming HA | 96 | VC local only |
| Live rollout / mesh | 84 | 34/34 L2; 34% of catalog-100 |
| Durable ingestion | 83 | ~46% coverage / 28 live sources |
| White Label | 78 | Real Super Terminal builder brand prove; no portal |
| Ops / honesty | 94 | No fake COMPLETE; status on light mesh |

**Overall (binding): 96 / 100 — NOT COMPLETE**  
**VERIFIED_COMPLETE count: 1**

---

## Delta vs prior tip (`94325d6` = 95)

1. Mesh 24→**34** with honest regional symbols (not synthetic TOB padding).
2. Mesh L2 **canonical-adopted** (closes “live but not on bus” gap).
3. Jupiter thickened with decode + simulate (still not signed fill).
4. White Label prove no longer theaters a hand-built terminal pack.
5. Fill paper attaches measured L2 book-walk / impact (still `live_fill=false`).

## What would raise the binding score further

1. Armed Binance testnet → measured `live_fill=true` (+VC candidate).
2. Armed Solana key + `JUPITER_LIVE_EXECUTION` → signed submit (+VC candidate).
3. Additional honest venues / keyed sources toward catalog 100%.
4. Cloud multi-AZ HA evidence beyond local streaming.
5. Full White Label customer portal (out of WOW scope).

## Honesty

- Prefer NOT COMPLETE over theater.
- quote ≠ execution; decode/simulate ≠ signed broadcast.
- Local streaming HA ≠ cloud multi-AZ.
- Paper/protocol fill + book-walk ≠ live venue fill.
