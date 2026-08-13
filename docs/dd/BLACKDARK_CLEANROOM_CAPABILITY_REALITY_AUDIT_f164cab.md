# BLACKDARK CLEAN-ROOM CAPABILITY REALITY AUDIT

**Auditor posture:** Independent adversarial clean-room. Docs, remediation ledgers, `COMPLETE`
labels, `product_complete` self-labels, commit messages, registers, desired scores, and green
test counts are **NOT** evidence. Only runtime probes, wiring inspection, negative paths, and
observed failure behavior are.

**Goal:** **DISPROVE** BLACKDARK completeness. Prefer NOT COMPLETE when any material surface
remains paper, synthetic, credential-gated, or geo-blocked.

---

```
REQUESTED TIP SHA:  f164cabbb203027579d0c18e9b8bd040b004d621
WORKSPACE HEAD:     f164cabbb203027579d0c18e9b8bd040b004d621   (MATCH at product audit time)
BRANCH:             cursor/95plus-recert-phase0-120d
TIP SUBJECT:        "Harden catalog failover against CoinGecko rate limits"
PRIOR BINDING:      5292cc7 = 97/100 NOT COMPLETE, VERIFIED_COMPLETE 1
```

**Working-tree caveat:** dirty/untracked `data/*` may be present. Audited product source is the
committed tip. **No product code modified by this audit commit.**

---

## INVENTORY / CLASSIFICATION

| Classification | Count / note |
|---|---|
| VERIFIED_COMPLETE | **1** (`postgres_streaming_ha_rpo_rto` — local; `cloud_multi_az=false`) |
| PARTIAL | bus, mesh/catalog, Jupiter quote+build+decode/sim+reverse, WL portal pack, fill paper, decision, ops bundle, PG product-path |
| UNVERIFIED | live venue fill (creds), Jupiter signed broadcast (wallet+flag) |
| LOCAL_EPHEMERAL_NOT_HA | dump/restore + product-path |
| Root `product_complete:True` | **0** |

---

## MANDATORY RUNTIME PROBES

### Mesh / catalog / ingestion
| Field | Observed |
|---|---|
| `CORE_PUBLIC_CEX_MESH` | **51** |
| mesh live / L2 | **52 / 51** (full_mesh prove) |
| canonical mesh adopted | **49** |
| full catalog-100 healthy | **100 / 100** price-health (`ok=true`) |
| depth breakdown | **venue_l2=46**, synthetic_mid=54, failed=0 |
| catalog `verified_complete` | **false** |
| Binance public | **vision mirror OK** (`data-api.binance.vision`) |
| honesty | synthetic_mid **not** claimed as institutional L2 |

### Jupiter / Fill / WL / HA
| Surface | Observed |
|---|---|
| quote + swap build + decode + simulate | **true** |
| reverse quote + latest blockhash | **true** |
| executed / signature / submit VC | **false** |
| fill `live_fill` | **false**; book_walk + cancel_replace shape ok |
| White Label portal pack | ok; client_gateway_ok=true; **hosted_custom_domain=false** |
| HA streaming | VC **true**; RPO≈25ms RTO≈127ms; `cloud_multi_az=false` |

### Honesty / tests
| Check | Observed |
|---|---|
| root `product_complete:True` | **0** |
| `tests/test_institutional_depth_completion.py` | **26 passed** |

---

## Surface scores (0–100)

| Surface | Score | Notes |
|---|---:|---|
| Canonical Truth Bus | 98 | Mesh canonical adoption |
| Decision → Intent → OMS | 97 | Live inputs; no self-grade theater |
| Venue FILL | 80 | Book-walk + cancel/replace; no live_fill |
| Jupiter DEX | 93 | Build/sim/reverse; no signed broadcast |
| Postgres product path | 93 | Ephemeral OMS |
| Postgres streaming HA | 96 | VC local only |
| Live rollout / mesh L2 | 92 | 51-target public L2 mesh |
| Catalog-100 price health | 94 | 100% with synthetic_mid labeled; not L2-complete |
| Durable ingestion | 93 | Catalog health rows + mesh continuum |
| White Label | 88 | Portal pack + gateway route map; not hosted SaaS |
| Ops / honesty | 96 | No fake COMPLETE / live_fill / cloud HA |

**Overall (binding): 98 / 100 — NOT COMPLETE**  
**VERIFIED_COMPLETE count: 1**

---

## Why NOT COMPLETE (binding)

1. **Catalog L2 ≠ 100%** — 54/100 venues are honest `synthetic_mid` (CG/global failover / DEX/perp proxies).
2. **`live_fill=false`** — paper + protocol shape only without testnet keys.
3. **Jupiter signature VC absent** — submit path implemented; no wallet/`JUPITER_LIVE_EXECUTION`.
4. **White Label PARTIAL** — in-process portal pack, not hosted custom-domain multi-tenant SaaS.
5. **HA local only** — `cloud_multi_az=false`.

## Delta vs `5292cc7` (97)

1. Full catalog-100 price-health prove (catalog rollout/ingest % → **100** with depth honesty).
2. Binance vision mirror failover for spot books + ingest registry URL.
3. Native L2: hotcoin / paribu / woox (+ brand aliases gemini_uk / cryptocom_us).
4. CoinGecko throttle + dead-id global mid failover (synthetic only).
5. CORE mesh **48→51**; WL portal client-gateway route map.

## Absolute rule

Green tests / HARDENED / self-`product_complete` ≠ COMPLETE.  
quote/decode/simulate ≠ signed broadcast.  
synthetic_mid catalog health ≠ institutional L2 mesh.  
Local streaming HA ≠ cloud multi-AZ.  
Paper fill ≠ live venue fill.
