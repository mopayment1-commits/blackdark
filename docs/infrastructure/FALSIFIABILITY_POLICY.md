# Falsifiability Policy (#1064)

**Cross-cutting policy** — NOT standalone. Applies to every signal · insight · recommendation · report · alert.

## Principle

Scientific integrity over false confidence: every output carries explicit "this would be wrong if..." conditions before publication.

## Mandatory condition types

Every output MUST include all three rule-based falsification types:

1. **Price-based** — numeric threshold (e.g. price moves > X% within Y days against direction)
2. **Time-based** — expiry / invalidation deadline
3. **Metric-based** — on-chain or volume metric change > W%

No vague conditions ("if the market changes"). Sprint 2 = rule-based only.

## Enforcement

- Missing falsification → output suppressed + epistemic gate reason `FALSIFICATION_CONDITIONS_MISSING`
- Condition met → insight auto-cancelled + #1021 gate with `FALSIFICATION_CONDITION_MET`
- Conditions visible in public methodology and linked from #1063 explanations

## API

```
GET  /api/platform/trust/falsifiability/status
POST /api/platform/trust/falsifiability/validate
GET  /api/platform/trust/falsifiability/e2e
```

## Integrations

#1021 Epistemic Humility · #1063 Explainability · #931 Claims Verification · #987 Internal Accuracy Ledger · #11 Signal Engine · #938 Decision Intelligence

## CI regression

`tests/test_trust_core_batch1064_1068.py` — fail if falsification conditions missing from validated payloads.
