# Explainability Policy (#1063)

**Cross-cutting policy** — NOT standalone module. Applies to every recommendation · alert · signal · insight · report.

## Mandatory "Why"

Every output MUST include an `explanation` object with 3 levels:

1. **One-line summary** (en + ar)
2. **Detailed breakdown** (rule-based reasons + confidence + freshness)
3. **Audit trail link**

## Sprint 2 rules

- Rule-based explanations only — no "the AI model believes"
- Risk scores require 3+ indicators with weights
- I DON'T KNOW gate outputs reason code + missing data + what would change conclusion
- CI regression: fail if explanation missing from API response

## API

```
GET  /api/platform/internal/infrastructure/explainability/status
POST /api/platform/internal/infrastructure/explainability/validate
GET  /api/platform/internal/infrastructure/explainability/e2e
```

## Integrations

#11 Signal Engine · #921 AI Provenance · #938 Decision Intelligence · #945 Provenance · #1021 Epistemic Humility · #987 Public Accuracy Ledger · #1030 Live Badge
