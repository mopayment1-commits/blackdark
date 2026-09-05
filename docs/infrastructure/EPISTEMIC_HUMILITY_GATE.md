# Epistemic Humility Gate (#1021 + merged #1067)

**Cross-cutting gate** inside Intelligence Ledger — NOT standalone.

## Principle

Abstain from fabricating high confidence when evidence conflicts or is insufficient. Output: **I DON'T KNOW**.

## Rule-based triggers (Sprint 2)

| Trigger | Condition |
|---------|-----------|
| `CONFLICT` | Quantifiable fact A contradicts fact B by > threshold % |
| `LOW_CONFIDENCE` | Confidence score < 5/10 |
| `INSUFFICIENT_DATA` | Sample size < 30 |
| `FALSIFICATION_CONDITION_MET` | #1064 falsification condition triggered |

No ML-generated confidence fabrication in Sprint 2.

## API

```
GET  /api/platform/trust/epistemic/status
POST /api/platform/trust/epistemic/evaluate
GET  /api/platform/trust/epistemic/e2e
```

## Integrations

#1064 Falsifiability · #11 Signal Engine · #921 AI Provenance · #938 Decision Intelligence · #1065 Public Ledger (abstentions published as `abstained`)

## Merged feature

#1067 (anti confidence fabrication) is fully merged into this gate — no separate module.
