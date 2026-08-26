# Flow-to-Price Event Correlator — #556

## Decision

Renamed from **Flow-to-Price Explanation Engine** to **Flow-to-Price Event Correlator** (Sprint 2 Intelligence Layer). Rule-based correlation — LLM optional later with constraints.

## Linguistic Framing (Mandatory)

| Use | Forbidden |
|-----|-----------|
| Candidate events in window | Likely drivers |
| Evidence strength | Confidence % (for causation) |
| Hypothesis labels | The cause is / Explanation Engine |
| Data completeness: X% | Confidence in cause |
| Temporal alignment: Y seconds | Whale alert = sell |

## Hypothesis Format

```
Hypothesis A: Whale inflow correlated. Evidence strength: 85.2 | Causation: Unverified.
Hypothesis B: Derivatives liquidation correlated. Evidence strength: 82.1 | Causation: Unverified.
```

Alternatives always shown. Competing-driver analysis mandatory.

## Acceptance Criteria

| Criterion | Implementation |
|-----------|----------------|
| Correlation ≠ causation explicit | Banner + per-event flags |
| Timestamps aligned | temporal_alignment_seconds on each candidate |
| Evidence links | evidence_id + evidence_link per event |
| Hypothesis labels | Hypothesis A/B/C format |
| No confidence % for causation | data_completeness_pct + temporal_alignment_seconds |
| Alternatives always shown | competing_hypotheses list |
| Rule-based only | llm_optional_later: true |

## API

```
GET /api/platform/intelligence-ledger/intelligence-layer/flow-to-price-correlator/status
GET /api/platform/intelligence-ledger/intelligence-layer/flow-to-price-correlator?event_id=btc_move_2026_08_26
```
