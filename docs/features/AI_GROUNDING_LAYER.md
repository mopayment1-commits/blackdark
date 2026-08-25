# #230 AI Market Data Grounding Layer

**Sprint 1 — AI Infrastructure (Middleware)**

## Overview

Ensures every AI response uses the same data contract as user-facing APIs. Tool-grounded retrieval via `blackdark_data_tool` — no model-only market facts. Middleware layer serving Portfolio AI, Market Radar, Smart Alert Engine, Scenario Engine, and Thesis Workspace.

Also known as **Verifiable AI Engine** / **Evidence-Linked Intelligence**.

## Acceptance Criteria

| Criterion | Implementation |
|-----------|----------------|
| No model-only market facts | `evidence[]` with source_api, timestamp, value, confidence |
| Tool-grounded retrieval | SYSTEM_PROMPT requires blackdark_data_tool before market facts |
| Oracle API #162 parity | Same endpoints via unified_api_platform |
| Fail-closed | API failure → "I'm unable to retrieve current data" |
| Audit trail | query, tools_called, data_returned, response_generated — 90 days |
| Weekly red-teaming | 100+ questions, 0% hallucination target |
| Middleware not standalone | Serves integrated surfaces only |

## #230 vs #262 MCP

| | #230 Grounding Layer | #262 MCP Server |
|--|---------------------|-----------------|
| Purpose | Internal AI quality | External agent access |
| Visibility | Middleware (not user-facing) | Developer-facing |
| Sprint | 1 | 2 |
| Traceability | Tool traceability + evidence | MCP protocol compliance |
| Shared rule | No model-only market facts | No model-only market facts |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/verifiable-ai/status` | Grounding layer status |
| `GET /api/platform/verifiable-ai/middleware/status` | Middleware + supported surfaces |
| `POST /api/platform/verifiable-ai/ground` | Ground a query with evidence |
| `GET /api/platform/verifiable-ai/audit` | Audit trail (90-day retention) |
| `GET /api/platform/verifiable-ai/red-team` | Weekly red-team verification |

## Files

- `bd_platform/verifiable_ai_engine.py` — core grounding engine
- `bd_platform/ai_grounding_middleware.py` — surface middleware
- `data/verifiable_ai_engine_seed.json` — configuration
- `data/ai_grounding_redteam_seed.json` — 100+ red-team questions
- `bd_platform/mcp_ai_server.py` — #262 integration (same grounding rules)
