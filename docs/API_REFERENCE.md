# BLACKDARK API Reference (Buyer Requirement #1 / #5)

## Decision API v1 (commercial contract)

Institutional Financial Intelligence API. Sales-issued per-tenant keys. Not the Trust OS web session.

| Method | Path | Auth |
|--------|------|------|
| GET | `/api/v1` | none (discovery) |
| GET | `/api/v1/openapi.json` | none |
| POST | `/api/v1/keys` | admin (`X-Admin-Key`) — sales-led issuance |
| GET | `/api/v1/oracle/{symbol}` | `X-API-Key` scope `oracle:read` |
| POST | `/api/v1/oracle/{symbol}/certificate` | `X-API-Key` scope `oracle:read` |
| GET | `/api/v1/accuracy` | `X-API-Key` scope `accuracy:read` |
| GET | `/api/v1/feed` | `X-API-Key` scope `feed:read` |
| WS | `/api/v1/feed/ws` | `Authorization` / `X-API-Key` scope `feed:ws` (query keys rejected) |
| GET | `/api/v1/audit` | `X-API-Key` scope `audit:read` |
| GET | `/api/v1/usage` | `X-API-Key` |
| POST/GET | `/api/v1/webhooks` | `X-API-Key` scope `webhooks:write` |
| POST | `/api/v1/webhooks/test` | `X-API-Key` scope `webhooks:write` |
| DELETE | `/api/v1/webhooks/{id}` | `X-API-Key` scope `webhooks:write` |

See `docs/DECISION_API_V1.md`. Legacy `/api/b2b/feed` (shared house key) is deprecated; successor `/api/v1/feed`.

## Base URL
- Local: `http://localhost:8080`
- GraphQL: `http://localhost:8080/graphql`
- OpenAPI: `http://localhost:8080/docs` | export: `/api/docs/openapi.json` | Decision API: `/api/v1/openapi.json`

## Health & Infrastructure
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health/live` | App liveness |
| GET | `:8180/health/live` | Sidecar liveness (<10ms) |
| GET | `/health/ready` | DB + Redis readiness |
| GET | `/api/infra/metrics` | RAM/CPU + efficiency |
| GET | `/api/services/status` | Microservices + bus |

## Arbitrage & Execution
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/arbitrage/opportunities` | Live scan results |
| GET | `/api/low-latency/status` | WS book hub stats |
| GET | `/api/risk/status` | Slippage/poisoning/stop-loss |
| POST | `/api/risk/freeze` | Freeze trading |
| POST | `/api/execution/panic` | Emergency halt |

## Oracle & ML
| Method | Path | Description |
|--------|------|-------------|
| GET | `/oracle/{symbol}?ux_mode=beginner\|pro&lang=en` | Primary Oracle + constitution enrich (English-only UI) |
| GET | `/oracle-accuracy` · `/oracle/accuracy` | Public Accuracy Ledger page (English) |
| GET | `/api/oracle/accuracy/public` | Public track record + proof_chain |
| GET | `/api/oracle/audit-chain` | Immutable hash chain |
| GET | `/api/oracle/audit-chain/verify` | Chain integrity check |
| GET | `/api/oracle/net-edge-truth` | Net-Edge Truth status (D3) |
| GET | `/api/oracle/half-life` | Opportunity Half-Life stats (D4) |
| GET | `/api/oracle/signals` | Sovereign Signal Registry (D8) |
| GET | `/api/oracle/persona-clarity/demo` | Persona Clarity English-first (D7) |
| GET | `/api/due-diligence/evidence-pack` | Full Evidence Pack (Whale/Admin) |
| GET | `/api/due-diligence/evidence-pack/public-summary` | Redacted public teaser |

## Heroes Strategy & Section Z
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/heroes/strategy` | Binding heroes + Section Z map |
| GET | `/api/audience/entry?audience=` | Section H entry routing |
| POST | `/api/oracle/decision-certificate` | Build Decision Certificate |
| GET/POST | `/api/locked-predictions` | Glass Box sealed forecasts |
| POST | `/api/discipline-mirror/answer` | Private follow-up Yes/No |
| GET | `/api/discipline-mirror/me` | Private Discipline Mirror |
| GET | `/api/accuracy/monthly-losing-report` | Public losing-trade sample |
| GET | `/api/audit-challenge` | Hash-chain challenge pack |
| GET | `/api/whale/signal-vs-noise` | Whale Signal vs Noise |
| POST | `/api/whale/stealth-advisor` | Whale stealth sizing advisory |
| GET | `/api/mev/sandwich-report` | Shareable MEV/Sandwich posture |
| GET | `/api/glass-box/challenge` | Glass Box Challenge ready pack |
| GET | `/api/fund/emerging-terminal` | Emerging Fund Terminal pack |
| GET | `/api/compliance/footer` | Anti-Hype footer block |
| GET | `/api/alerts/generosity` | Alert posture vs TV-style caps |
| GET | `/robots.txt` · `/sitemap.xml` | Crawl / GEO surfaces |
| GET | `/admin/plan` · `/api/plan/audit` | Plan audit (admin/LOCAL_DEV) |
| GET | `/admin/roadmap` · `/api/roadmap/audit` | Roadmap audit (admin/LOCAL_DEV) |

## Data & Sentiment
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/ingestion/status` | Source health |
| GET | `/api/sentiment/overview` | NLP sentiment indices |
| GET | `/api/options/overview` | Deribit options data |

## B2B
| WS | `/ws/b2b/feed?api_key=...` | Institutional live feed |

## GraphQL Queries
```graphql
query {
  health { status probe }
  oracleAccuracy { totalPredictions recentHitRatePercent }
  topArbitrage(limit: 5) { asset netProfitUsdt }
  riskStatus { tradingFrozen maxSlippageBps }
  dataSources { totalSources }
}
```

## Microservices Ports
| Service | Port | Health Sidecar |
|---------|------|----------------|
| web | 8080 | 8180 |
| aggregator | 8091 | 8191 |
| arbitrage | 8092 | 8192 |
| ingestion | 8093 | 8193 |

## Environment (Production)
```env
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
SERVICE_MODE=web
SENTIMENT_GATE_ENABLED=true
SENTIMENT_TWITTER_MOCK_ENABLED=false
TWITTER_BEARER_TOKEN=...
RISK_MAX_SLIPPAGE_BPS=80
RISK_STOP_LOSS_PCT=2.0
```
