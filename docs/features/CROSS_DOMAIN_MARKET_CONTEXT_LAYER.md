# Cross-Domain Market Context Layer — #524 Epic

## Decision: 🟢 Proceed — as Layer — Sprint 2

Features #523, #525, #526–#530 merged into single epic:

**Cross-Domain Market Context Layer**

Renamed from "Cross-Domain Decision Intelligence Layer" / "Cross-Market Decision Intelligence Engine".

| Original | Sub-Module (Task, Not Ticket) |
|----------|-------------------------------|
| #523 Cross-Domain Decision Intelligence | `derivatives_context` |
| #525 Cross-Domain Decision Intelligence Layer | `onchain_flow_context` |
| #526 Social+On-chain+Dev | `social_onchain_dev` |
| #527 Custom query (Dune-style) | `custom_query` |
| #528 Entity-focused | `entity_focused` |
| #529 Fundamental | `fundamental` |
| #530 Cross-Market Decision Intelligence Engine | `market_wide_aggregation` |

## Architecture

```
Intelligence Layer (Sprint 2)
└── #524 Cross-Domain Market Context Layer (Epic)
    ├── #523 derivatives_context
    ├── #525 onchain_flow_context
    ├── #526 social_onchain_dev
    ├── #527 custom_query
    ├── #528 entity_focused
    ├── #529 fundamental
    └── #530 market_wide_aggregation

Dependencies:
├── #316 Epistemic Output Framework
├── Data Layer (#516, #501, #503)
└── On-Chain Layer (#506, #508)
```

## Mandatory Rules

| Rule | Implementation |
|------|----------------|
| No standalone UI | API/feed for UI modules only |
| Fact/Inference/Hypothesis | UI labels: green/blue/amber with tags |
| No action claims | Context relevance ≠ Buy/Sell — supports/contradicts hypothesis |
| Source/freshness/confidence | Every conclusion has metadata |
| No single-source domination | Rule-based dominance check (#530) |
| Stale-source penalties | Confidence reduced for stale data (#530) |
| Rule-based first | ML deferred to Wave 3 |

## Output Structure

```
What changed → Why → Confirmation → Risk → Confidence → Context relevance
```

Context relevance (internal): `This factor supports/contradicts [hypothesis]` — never recommendation.

## API

| Endpoint | Purpose |
|----------|---------|
| `GET .../intelligence-layer/market-context/status` | Epic status |
| `GET .../intelligence-layer/market-context` | Full context panel |
| `GET .../intelligence-layer/market-context/sub-module/{id}` | Sub-module feed (#523-530) |

## Acceptance Criteria

- Fact/Inference/Hypothesis separated ✅
- No unsupported action claim ✅
- Source/freshness/confidence for every conclusion ✅
- No single-source domination without rule ✅
- Stale-source penalties ✅
- Explainable ✅
- No standalone UI ✅
