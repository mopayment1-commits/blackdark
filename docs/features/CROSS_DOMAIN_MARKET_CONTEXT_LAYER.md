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
| #599 Social-to-On-Chain Confirmation Engine | `hype_vs_reality_signal` (renamed **Hype vs Reality Signal**) |

## #599 — Hype vs Reality Signal (→ #524 sub-module)

Renamed from "Social-to-On-Chain Confirmation Engine". No "Engine" in legal name.

### Four States (badge on every signal)

| State | Badge | Condition | User Message |
|-------|-------|-----------|--------------|
| Confirmed | 🟢 | Social ↑ + On-Chain ↑ | Behavior-backed — signals aligned |
| Social-Only | 🟡 | Social ↑ + On-Chain → | Noise only — no on-chain confirmation |
| On-Chain-Only | 🔵 | On-Chain ↑ + Social → | Silent move — potential early signal |
| Contradictory | 🔴 | Social ↑ + On-Chain ↓ | Contradiction — data sources disagree |

### Acceptance

- No forced consensus on ambiguous inputs
- Contributors / freshness / confidence shown on every assessment
- Historical validation displayed (e.g. 83% Contradictory → correction within 7 days)
- No chatbot advisor role — data quality only, not buy/sell

### Integrations

- #443 Event Monitor → social input
- #408 Smart Money + #577 On-Chain Metrics → on-chain input
- #474 Daily Brief → signal quality summary
- #429 Intelligence Ledger + #403 Arbitrage Scanner → badge on signals
- Market Radar → badge on dashboard

### Routes

```
GET .../intelligence-layer/hype-vs-reality?asset=BTC
GET .../intelligence-layer/hype-vs-reality/status
GET .../intelligence-layer/market-context/sub-module/599
```

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
    ├── #530 market_wide_aggregation
    └── #599 hype_vs_reality_signal (Hype vs Reality Signal)

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
| `GET .../intelligence-layer/market-context/sub-module/{id}` | Sub-module feed (#523-530, #599) |
| `GET .../intelligence-layer/hype-vs-reality` | #599 Hype vs Reality Signal panel |

```bash
.venv/bin/python -m pytest tests/test_cross_domain_market_context_batch.py tests/test_hype_vs_reality_signal_batch.py -q
```

## Acceptance Criteria
- No unsupported action claim ✅
- Source/freshness/confidence for every conclusion ✅
- No single-source domination without rule ✅
- Stale-source penalties ✅
- Explainable ✅
- No standalone UI ✅
