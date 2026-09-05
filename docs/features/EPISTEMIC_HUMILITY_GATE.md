# Epistemic Humility Gate — Sprint 2 (Intelligence Ledger)

Cross-cutting epistemic policy engine merged into Intelligence Ledger — **not** a standalone service.

## Purpose

When supporting evidence conflicts, statistical confidence is low, or sample size is insufficient, the gate **abstains** with an explicit **"I DON'T KNOW"** output instead of a confident buy/sell guess.

## Surface

```
GET  /api/intelligence/gate/status
GET  /api/intelligence/gate/methodology
POST /api/intelligence/gate/evaluate
POST /api/intelligence/gate/publish
GET  /api/intelligence/gate/hit-rate
GET  /api/intelligence/gate/e2e
```

Also nested under Intelligence Ledger:

```
GET  /api/platform/intelligence-ledger/gate/status
POST /api/platform/intelligence-ledger/gate/evaluate
```

## Rule-based triggers (deterministic — no ML in Sprint 2)

| Code | Condition |
|------|-----------|
| `CONFLICT` | `abs(A-B)/max(|A|,|B|)*100 > 15%` |
| `LOW_CONFIDENCE` | `confidence_score < 5/10` |
| `INSUFFICIENT_DATA` | `sample_size < 30` |
| `STALE_DATA` | `data_age_hours > 24` |

## Output on abstain

- Token: `"I DON'T KNOW"`
- Reason code
- Evidence summary
- Missing data identified
- Auto disclaimer (EN + AR): *"بيانات غير كافية لرؤى موثوقة — لا توقع ولا تأكيد."*

## Integrations

| Ref | Behavior |
|-----|----------|
| #11 Signal Engine | Gate before publish; rejected → logged |
| #921 AI Provenance | Gate decision in footer metadata |
| #938 Decision Intelligence | Unsupported hypothesis → blocked |
| #987 Accuracy Ledger | Abstentions = `unresolved_abstained` |
| #945 Provenance | Requires stable provenance layer |

## Fee DB

Every evaluation logs: `analysis_cost_usd`, `evidence_count`, `confidence_score`, `abstention_reason`, `user_tier`.

## Monitoring

Internal hit-rate panel — target **20–40%** abstention = healthy epistemic humility.

## Non-custodial

Gate operates on public data + metadata only — no wallet data.
