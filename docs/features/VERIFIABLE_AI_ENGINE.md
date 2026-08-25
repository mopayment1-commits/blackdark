# Verifiable AI Engine — #230 (Sprint 1, Core AI Layer)

Evidence-Linked Intelligence: every AI insight anchored to canonical market data with traceable source links.

> "Every AI-generated insight is anchored to canonical market data with traceable source links. No answer without evidence."

## Institutional Rules

| Rule | Implementation |
|------|----------------|
| No model-only facts | `evidence[]` required with `source_api`, `timestamp`, `value`, `confidence` |
| Tool-grounded retrieval | `blackdark_data_tool` before any market fact |
| Oracle API parity | Same endpoints as user-facing Unified API (#162) |
| Fail-closed | No source → "I don't have verified data for that" |
| Disclaimer mandatory | Every response includes non-hideable disclaimer |
| Audit trail | 90-day retention in `data/verifiable_ai/audit_trail.jsonl` |
| All tiers | Quality guarantee, not gated |

## Prerequisites

| Ticket | Role |
|--------|------|
| #208 Source Registry | Canonical source map |
| #219 Freshness Assurance | Timestamp + latency metadata |
| #162 Oracle API | Same data path for AI and users |

## Integrated Surfaces

- Portfolio AI
- Market Radar / AI Chat (`chat_service.py`)
- Oracle API (`unified_api_platform.py`)
- Decision Intelligence Engine
- Smart Alert Engine
- Scenario Engine

## Response Contract

```json
{
  "answer": "...",
  "evidence": [
    {
      "fact": "BTC verdict WAIT (confidence 62%)",
      "source": "Oracle API v2.1",
      "source_api": "Oracle API v2.1",
      "timestamp": "2026-08-25T13:20:00Z",
      "value": {"verdict": "WAIT", "confidence_score": 62},
      "confidence": "verified",
      "freshness_ms": 120,
      "source_link": "/api/v1/platform/oracle?asset=BTC",
      "citation_display": "Source: ... | Data verified at ..."
    }
  ],
  "confidence_badge": "Verified",
  "disclaimer": "This analysis is based on BLACKDARK canonical data. It does not constitute financial advice.",
  "disclaimer_hideable": false,
  "view_source_data": {"enabled": true, "links": ["..."]}
}
```

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/verifiable-ai/status` | Module status + acceptance criteria |
| `POST /api/platform/verifiable-ai/ground` | Ground a query with evidence |
| `GET /api/platform/verifiable-ai/audit` | Audit trail (90-day retention) |

## Confidence Badges

| Badge | Meaning |
|-------|---------|
| Verified | All facts cross-referenced with canonical Oracle API |
| Partial | Some facts verified; others unavailable |
| Simulated | No verified data — fail-closed response only |

## System Prompt Rule

```
You must call the BLACKDARK data tool before stating any market fact.
If the tool returns no data, say 'I don't have current data for that.'
```

## Related

- `bd_platform/verifiable_ai_engine.py` — core middleware
- `bd_platform/source_registry_provenance.py` — #208 canonical sources
- `bd_platform/freshness_assurance.py` — #219 freshness metadata
- `bd_platform/unified_api_platform.py` — #162 Oracle API
- `chat_service.py` — AI chat integration
