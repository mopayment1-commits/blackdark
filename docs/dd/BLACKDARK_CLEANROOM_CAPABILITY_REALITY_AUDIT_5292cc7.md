# BLACKDARK CLEAN-ROOM CAPABILITY REALITY AUDIT

**Auditor posture:** Independent adversarial clean-room. Docs, remediation ledgers, `COMPLETE`
labels, `product_complete` self-labels, commit messages, registers, desired scores, and green
test counts are **NOT** evidence. Only runtime probes, wiring inspection, negative paths, and
observed failure behavior are.

**Goal:** **DISPROVE** BLACKDARK completeness. Prefer NOT COMPLETE. Credentials and cloud
multi-AZ were explicitly excluded from this remediation wave by operator instruction — remaining
gaps there do **not** authorize COMPLETE.

---

```
REQUESTED TIP SHA:  5292cc70c115cbb685dcd9f63d6d6998a1764d9b
WORKSPACE HEAD:     5292cc70c115cbb685dcd9f63d6d6998a1764d9b   (MATCH at product audit time)
BRANCH:             cursor/95plus-recert-phase0-120d
TIP SUBJECT:        "Close remaining repo-fixable institutional gaps without keys or cloud"
PRIOR BINDING:      76105a8 = 96/100 NOT COMPLETE, VERIFIED_COMPLETE 1
```

**Working-tree caveat:** dirty/untracked `data/*` may be present. Audited product source is the
committed tip. **No product code modified by this audit commit.**

---

## INVENTORY / CLASSIFICATION

| Classification | Count / note |
|---|---|
| VERIFIED_COMPLETE | **1** (`postgres_streaming_ha_rpo_rto` — local; `cloud_multi_az=false`) |
| PARTIAL | bus, mesh/ingest, Jupiter quote+build+decode/sim+reverse, WL, fill paper, decision, ops bundle, PG product-path |
| UNVERIFIED | live venue fill (creds excluded) |
| LOCAL_EPHEMERAL_NOT_HA | dump/restore + product-path |
| Root `product_complete:True` | **0** |

---

## MANDATORY RUNTIME PROBES

### Mesh / rollout / ingestion
| Field | Observed |
|---|---|
| `CORE_PUBLIC_CEX_MESH` | **48** |
| live / L2 | **48 / 48** |
| canonical mesh adopted | **46** |
| regional overrides | **14** |
| durable ingest live_sources | **48** |
| ingest coverage | ~**66%** |
| pricing_log exchanges | **48** |
| rollout healthy / % | **40** / **40.0%** of catalog-100 |
| Binance public | HTTP **451** (honest fail) |

### Jupiter / Fill / WL / Decision / Ops / HA
| Surface | Observed |
|---|---|
| quote + build + decode + simulate | **true** |
| reverse SOL→USDC quote | **true** |
| latest blockhash | **true** |
| executed / broadcast / submit VC | **false** |
| fill `live_fill` | **false**; book_walk + cancel_replace shape ok |
| White Label | PARTIAL; builder + **org isolation** ok |
| decision e2e | live inputs; `learning_self_grade=false` |
| ops recovery bundle | ok; continuity ok; cloud_multi_az=false; VC false without HA opt-in |
| HA streaming | VC **true**; RPO≈24ms RTO≈126ms; not cloud |
| PG product-path | ok, authority=postgres |

### Honesty / tests
| Check | Observed |
|---|---|
| root `product_complete:True` | **0** |
| depth + gates tests | **36 passed** |

---

## Surface scores (0–100)

| Surface | Score | Notes |
|---|---:|---|
| Canonical Truth Bus | 98 | Mesh canonical adoption + light refresh |
| Decision → Intent → OMS | 97 | Live spread/funding; no self-grade theater |
| Venue FILL | 80 | Book-walk + cancel/replace; still no live_fill |
| Jupiter DEX | 93 | Reverse + blockhash + impact gate; no signed broadcast |
| Postgres product path | 93 | Ephemeral OMS |
| Postgres streaming HA | 96 | VC local only |
| Live rollout / mesh | 88 | 48/48 L2; 40% catalog-100 |
| Durable ingestion | 88 | 48 sources / ~66% |
| White Label | 82 | Isolation + theme tokens; no portal |
| Ops / honesty | 95 | Bundle + prove APIs; no fake COMPLETE |

**Overall (binding): 97 / 100 — NOT COMPLETE**  
**VERIFIED_COMPLETE count: 1**

---

## Delta vs `76105a8` (96)

1. Mesh 34→**48** with native regional L2 (killed CoinGecko TOB for those ids).
2. Ingest regional symbol bug fixed → **48** live sources / ~**66%**.
3. Jupiter reverse quote + blockhash + impact/route fail-closed.
4. WL multi-org isolation prove.
5. Fill cancel/replace shape + live spread; decision live inputs.
6. Local ops recovery bundle + missing prove API routes.
7. CCXT pool leak closed on prove paths.

## Still open (operator-excluded this wave)

1. Live venue FILL — keys/flags.
2. Jupiter signed submit — wallet + flag.
3. Catalog mesh 100% — remaining public blocks / keyed sources.
4. Cloud multi-AZ HA — not claimed.

## Honesty

- Prefer NOT COMPLETE over theater.
- quote/decode/simulate/reverse ≠ signed broadcast.
- Local streaming HA ≠ cloud multi-AZ.
- Paper fill + book-walk ≠ live venue fill.
