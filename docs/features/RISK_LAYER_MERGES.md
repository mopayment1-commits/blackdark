# Risk Layer Merges — Features #453, #459, #461, #462, #463

## Summary

Five medium-priority features merged into existing layers — no standalone modules.

| Feature | Name | Merged Into |
|---------|------|-------------|
| #453 | Portfolio Stress Test | #410 Capital Protection Controls |
| #459 | Age Consumed / Dormancy | #408 Smart Money Flow Tracker |
| #461 | Beginner Decision Mode | UI/UX Layer (+ #468 Decision-First) |
| #462 | Collateral Risk | #460 Diligence Risk Scoring |
| #463 | Correlation & Contagion Risk | #410 Capital Protection Controls |

---

## #453 — Portfolio Stress Test (→ #410)

Renamed from "AI Portfolio Stress Testing Simulator" — no AI buzzword.

### 5 Mandatory Scenarios

1. Max drawdown shock
2. Correlation spike
3. Liquidity freeze
4. Stablecoin depeg
5. Exchange insolvency

### Acceptance Criteria

| Criterion | Status |
|-----------|--------|
| Coverage ≥80% | 100% (5/5 scenarios) |
| Repeatable tests | Deterministic execution |
| No uncontrolled blast radius | `controlled_blast_radius: true` per scenario |
| Full documentation | Assumptions visible per scenario |

### Routes

```
GET /api/platform/intelligence-ledger/portfolio-ai/capital-awareness/stress-test
```

---

## #463 — Correlation & Contagion Risk (→ #410)

| Capability | Description |
|------------|-------------|
| Correlation matrix | 30-day rolling for portfolio assets |
| Contagion risk | Sector + chain + stablecoin dependency |
| Stress integration | Correlation → 1.0 scenario loss estimate |

Cancelled SLA: response ≤2s, accuracy ≥95%, uptime 99%, real-time update.

### Routes

```
GET /api/platform/intelligence-ledger/portfolio-ai/capital-awareness/correlation-matrix
GET /api/platform/intelligence-ledger/portfolio-ai/capital-awareness/contagion-risk
```

---

## #459 — Age Consumed / Dormancy (→ #408)

| Output | Description |
|--------|-------------|
| `dormancy_score` | 0–100 spike intensity |
| `whale_label` | e.g. ancient_whale_awakening |
| `impact_estimate_pct` | Historical correlation-based |

Mandatory: chain methodology (UTXO vs Account), transfer filtering, historical validation.

### Routes

```
GET /api/platform/intelligence-ledger/onchain-layer/smart-money-flow/status
GET /api/platform/intelligence-ledger/onchain-layer/smart-money-flow
GET /api/platform/intelligence-ledger/onchain-layer/smart-money-flow/reconciliation-tests
```

---

## #461 — Beginner Decision Mode (UI/UX)

Progressive disclosure: **Summary → Details → Raw Data**

- Risk warning always visible (cannot be hidden)
- Same calculations — presentation layer only
- Merged with #468 Decision-First Mode

### Route

```
GET /api/platform/intelligence-ledger/ui/beginner-decision-mode/status
```

---

## #462 — Collateral Risk (→ #460)

Transparent grade (A–F) with breakdown:

- Volatility %
- Liquidity depth
- Concentration %
- Oracle health
- Depeg history

### Integrations

- **#438 DeFi Scanner** — `collateral_grade_462` on each opportunity
- **#410 Capital Protection** — alert when grade < B

---

## Tests

```
43 passed — capital awareness + risk layer merges + diligence risk scoring
```
