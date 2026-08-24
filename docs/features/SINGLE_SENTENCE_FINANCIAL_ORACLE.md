# Single-Sentence Financial Oracle — Feature #125

## Commercial face of BLACKDARK

User enters an asset symbol → one compliant analysis line.

## Output format (legal-safe)

```
BTC — Analysis: Bullish | Confidence: 78% | Reason: 24h volume $1.2B — institutional liquidity tier
```

**Never uses:** "Buy Now", "Do Not Touch", "اشترِ الآن"

## Rules

1. Analysis labels: `Bullish` / `Neutral` / `Bearish` only
2. Exactly **one** data-driven reason
3. Mandatory disclaimer (non-hideable): *"هذا تحليل آلائي، ليس توصية مالية. DYOR."*
4. Bearish/Neutral always include a reason
5. Free tier: **3 queries/day** (Pro = unlimited)

## API

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/oracle/single-sentence?asset=BTC` | Run oracle |
| `GET /api/oracle/single-sentence?asset=BTC` | Same (oracle router) |
| `GET /api/platform/oracle/single-sentence/status` | Feature metadata |

## Widget metadata

Response includes `widget` block for UI embedding:
- `input_placeholder`: "Enter asset (e.g. BTC, ETH)"
- `button_label`: "Analyze"

## Acceptance

- Response ≤ 2 seconds (`sla_met`)
- Accuracy estimate ≥ 95%
- Regulatory compliance via `regulatory_compliance_guard`
