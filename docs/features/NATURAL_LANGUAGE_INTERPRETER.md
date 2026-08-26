# Natural Language Interpreter — #573

## Decision

**Proceed — Sprint 2 (UX Layer).** LLM + rule-based guardrails.

Renamed from **Natural_Language_Interpreter** → **Natural Language Interpreter**.

| Rule | Implementation |
|------|----------------|
| No advisory answers | `_BANNED_ADVISORY_PATTERNS` + `_advisory_redirect()` |
| Permission checks | `check_permission()` per tool schema |
| Safe fallback | `_safe_fallback()` for empty/ambiguous queries |
| Deterministic schemas | `build_tool_schemas()` |
| No unsupported execution | `_execute_tool()` whitelist only |

## Advisory Handling

| Query | Response |
|-------|----------|
| "What is Bitcoin's exchange flow?" | Routes to `exchange_flow` tool |
| "Should I buy Bitcoin?" | Blocked — redirects to exchange flow data |

## Supported Tools

| Tool ID | Permission | Route |
|---------|------------|-------|
| exchange_flow | authenticated | `/onchain-layer/exchange-intelligence` |
| market_conditions | guest | `/intelligence-layer/market-conditions` |
| onchain_metrics | guest | `/onchain-layer/metrics-library` |
| portfolio_tracker | authenticated | `/portfolio-layer/multi-chain-tracker` |
| news_panel | guest | `/intelligence-layer/ai-content/news` |
| nvt_context | guest | `/data-layer/protocol-valuation` |

## API

```
GET /api/platform/intelligence-ledger/ux-layer/natural-language/status
GET /api/platform/intelligence-ledger/ux-layer/natural-language/schemas
GET /api/platform/intelligence-ledger/ux-layer/natural-language?query=...
GET /api/platform/intelligence-ledger/ux-layer/natural-language/reconciliation-tests
```

## UI

```
GET /ask
```

## Acceptance Criteria

| Criterion | Implementation |
|-----------|----------------|
| Deterministic tool schemas | `build_tool_schemas()` |
| Permission checks | `check_permission()` |
| Ambiguous-query handling | `_safe_fallback("ambiguous_query")` |
| No unsupported execution | Whitelist in `_execute_tool()` |
| No advisory answers | `_is_advisory_query()` + redirect |
