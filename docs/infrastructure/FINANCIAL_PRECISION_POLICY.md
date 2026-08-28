# Financial Precision Policy (#1032)

Cross-cutting engineering policy — **NOT** a standalone module. Enforces `Decimal`/fixed-point in every financial calculation path; binary `float` is forbidden in settlement scope.

## Rule

| Context | Type | Precision | Rounding |
|---------|------|-----------|----------|
| Crypto | `Decimal` | 8 dp | round-half-up |
| Fiat | `Decimal` | 2 dp | round-half-up |
| Fee rates | `Decimal` | 7 dp | half-even (legacy `rate()`) |

`float` remains acceptable for **market-data display** and order-book normalization heuristics outside settlement functions.

## Scoped modules

| Ref | Domain |
|-----|--------|
| #981 | Profitability / PnL |
| #908 | Stripe billing |
| #959 | Reference pricing |
| #1004 | Standardized financial metrics |
| #986 | Protocol KPIs |
| #1007 | Token allocation |
| #1009 | Vesting schedule |
| #992 | Real volume |
| #1029 | Immutable audit (Decimal-originated hashes) |
| #945 | Provenance audit trail |

## Enforcement

1. **Type enforcement** — `money_decimal.crypto_money()` / `fiat_money()` at settlement boundaries
2. **CI lint** — `scripts/financial_precision_lint.py` scans settlement functions; build fails on `float()` violations
3. **Production gate** — `check_production_gate_1032()` blocks deploy if lint fails

## Audit metadata (#945)

Every financial calculation may attach:

```json
{
  "type_used": "Decimal",
  "precision": 8,
  "rounding_method": "round_half_up",
  "methodology_version": "1.0.0",
  "financial_precision_ref": 1032
}
```

## API

```
GET /api/platform/financial-precision/status
GET /api/platform/financial-precision/production-gate
GET /api/platform/financial-precision/lint
GET /api/platform/financial-precision/audit-trail
GET /api/platform/financial-precision/e2e
```

## Sprint 0

Policy enforced **before** any financial feature ships. No production deploy without passing lint gate.

## Module

- `bd_platform/financial_precision_policy_engine.py`
- `money_decimal.py` — canonical Decimal helpers
- `data/financial_precision_seed.json`
- `scripts/financial_precision_lint.py`
