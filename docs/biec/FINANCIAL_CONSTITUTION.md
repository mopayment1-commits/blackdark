# Financial Constitution

**Program:** BLACKDARK INSTITUTIONAL ENGINEERING CONSTITUTION (BIEC)  
**Document role:** Sole monetary precision and financial-path authority  
**Article schema:** Atomic principle with machine-verifiable predicate

---

### ART-FIN-001

| Field | Value |
|-------|-------|
| Principle | Authoritative monetary storage uses exact decimal types with declared scale and precision. |
| Verification predicate | Schema audit detects zero binary floating-point columns on financial tables. |
| Independence | Does not delegate to any other constitution article. |

### ART-FIN-002

| Field | Value |
|-------|-------|
| Principle | New financial storage columns cannot use binary floating-point types. |
| Verification predicate | Schema diff introducing binary floating-point on financial table class yields FAIL. |
| Independence | Complements ART-FIN-001 without restating storage rule. |

### ART-FIN-003

| Field | Value |
|-------|-------|
| Principle | Authoritative fee and profit comparison paths use exact decimal arithmetic before persist or execution authorization. |
| Verification predicate | Hot-path audit detects zero native floating-point casts on declared money comparison boundaries. |
| Independence | Does not delegate to any other constitution article. |

### ART-FIN-004

| Field | Value |
|-------|-------|
| Principle | Threshold boundary comparisons on money paths satisfy exact decimal invariants at declared quantum. |
| Verification predicate | Property invariant test at minimum quantum fails on floating-point reintroduction. |
| Independence | Complements ART-FIN-003 without restating path scope. |

### ART-FIN-005

| Field | Value |
|-------|-------|
| Principle | Portfolio holdings and rebalance preview read from one authoritative read model. |
| Verification predicate | UI and API rebalance preview hash divergence for same subject is FAIL. |
| Independence | Complements ART-PLAT-004 without restating platform ownership. |

### ART-FIN-006

| Field | Value |
|-------|-------|
| Principle | Audit export of financial aggregates preserves decimal string representation without silent rounding. |
| Verification predicate | Export round-trip equality test fails on precision loss beyond declared scale. |
| Independence | Does not delegate to any other constitution article. |
