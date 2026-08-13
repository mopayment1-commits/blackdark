# BLACKDARK Decision API v1

Commercial Financial Intelligence contract. Separate from Trust OS (session cookie / Bearer user session).

## Binding rules

1. Customer authentication is a **per-org API key** (`bd_live_` / `bd_test_`). Keys are hashed at rest and shown once.
2. Issuance is **sales-led**: `POST /api/v1/keys` requires `X-Admin-Key` (MSA / Data License / SLA first).
3. The commercial URL prefix is `/api/v1`. Breaking changes require `/api/v2`. Deprecated paths get `Deprecation` + `Sunset` (≥12 months).
4. Customer keys never authorize admin, live execution, vault, ML training, or Prometheus `/metrics`.
5. Licensed use: internal decision support. Redistribution / model training requires a separate Data License.
6. Legacy `/api/b2b/feed` uses a shared house env key and is **deprecated** (sunset 13 Aug 2027). Successor: `/api/v1/feed`.

## Auth

```
X-API-Key: bd_live_…
Authorization: Bearer bd_live_…
```

WebSocket `/api/v1/feed/ws`: same headers. Query-string `api_key` is rejected (`1008 query_api_key_forbidden`).

## Scopes

`oracle:read` · `accuracy:read` · `feed:read` · `feed:ws`

## Quotas

Per-key RPM + RPD. Responses include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`. HTTP 429 includes `Retry-After`.

Optional universe allowlist: `DECISION_API_UNIVERSE=BTC,ETH,SOL`.

## Env

| Variable | Purpose |
|----------|---------|
| `DECISION_API_KEY_PEPPER` | HMAC pepper for key hashes (falls back to `SESSION_TOKEN_PEPPER`) |
| `DECISION_API_UNIVERSE` | Comma-separated licensed symbols |
| `METRICS_BEARER_TOKEN` | Prometheus scrape token (required in production unless unauthenticated override) |
| `METRICS_ALLOW_UNAUTHENTICATED` | Opt-in public `/metrics` (private networks only) |

## Error envelope

```json
{"error":"unauthorized","code":"unauthorized","message":"...","request_id":"...","api_version":"v1","status":401}
```

Every v1 response includes `X-Request-Id` and `X-API-Version: v1`.
