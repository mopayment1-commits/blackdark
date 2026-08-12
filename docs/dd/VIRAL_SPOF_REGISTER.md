# BLACKDARK — Capacity-Critical Single Points of Failure

Evidence context: viral surge lab @ Postgres+Redis+2 uvicorn workers  
(see `docs/dd/VIRAL_SURGE_EVIDENCE.md`).

| Component | Capacity risk | Failure effect | Mitigation (shipped) | Failover strategy | Monitoring | Recovery behavior |
|-----------|---------------|----------------|----------------------|-------------------|------------|-------------------|
| Web / uvicorn process | Medium — 2 workers on one host | All HTTP/API down if process dies | `WEB_CONCURRENCY≥2`; k8s HPA min 2 (`deploy/k8s`); load shed middleware | Multi-replica (`WEB_REPLICAS` / Railway numReplicas) behind LB | `/health/live`, `/health/ready`, `/health/viral` | Restart process; RL keys in Redis survive |
| Redis | High for viral HA | Per-process RL/inflight/cache only; weaker multi-replica coherence | Viral approval requires live Redis; connect neg-cache; memory fallback | Managed Redis (Railway/Upstash) with persistence optional (cache plane) | `redis_live` in `/health/viral`; `rate_limit_backend` | Clients reconnect; RL windows rebuild |
| Postgres | High for auth/sessions/history | Login/session/write paths fail; reads may degrade | Pool min/max under `VIRAL_MODE`; health ready gate | Managed PG HA / follower for reads (buyer infra) | `postgres_pool` in scale readiness; `pg_stat_activity` | Pool recovers; no permanent exhaustion observed at Stage E (10% sat) |
| External market providers | High for oracle freshness | Oracle slow/empty; **must not invent profit** | Fail-closed gas/fees; indicative labeling; oracle RL + semaphore | Multi-venue fallbacks already in market context; shed oracle class | Oracle p95 in load log; provider errors in logs | Quick cache + RL; cold oracle p95 ~650ms measured |
| Background workers (aggregator/arb) | Medium | Stale books if workers down | Separated service modes; web can run without aggregator | Scale aggregator replicas independently | Worker health sidecars | Restart workers; hub freshness rejects stale symbols |
| WebSocket hub (B2B) | Medium | Hub down → no B2B push; boot regression fixed (`async start`) | Connection cap `B2B_WS_MAX_CONNECTIONS`; heartbeat | Sticky sessions / Redis pubsub (future) for multi-replica | Hub `stats()` | Restart hub task; clients reconnect |
| Scheduler / flywheel | Low–Med | ML/jobs stop; not financial SoR | Feature flags; non-blocking enqueue | Disable non-critical jobs under load | Flywheel logs / admin | Restart scheduler |
| Payment callback path | High for revenue | Missed webhooks → entitlement lag | Signature required; fail closed on bad secret | PSP retries; durable outbox for email | Billing/webhook logs | Replay PSP events; no silent accept |
| AI / oracle compute | High under viral | Latency spike / 429 | `VIRAL_ORACLE_CONCURRENCY`, oracle RL, `/quick` micro-cache (Redis) | Cache hit collapse; shed to 429 | oracle_quick p95 in surge JSON | Cache + RL window drain (~60s) |
| DNS / load balancer / CDN | High at true global viral | Origin overload if CDN missing | Cache-Control on landing; docs recommend CDN for `/` + `/static` | Edge CDN (Cloudflare etc.) — **EXTERNAL** | CDN + uptime | Edge absorbs anonymous GETs |
| Shared in-memory state | Medium multi-replica | Split-brain RL/cache if Redis down | Redis backends for RL/inflight/quick cache when available | Require Redis for `viral_production_approved` | readiness backends fields | Memory fallback is weaker — viral gate fails closed without Redis |

## Scaling path (documented)

1. Origin: `WEB_CONCURRENCY=4`, `WEB_REPLICAS≥2`, `PG_POOL_MAX` sized to replicas×workers headroom  
2. Redis: shared `REDIS_URL`, `SERVICE_BUS_LOCAL=false`  
3. Edge: CDN for `/`, `/static`, compliance HTML  
4. Re-sign capacity: re-run `scripts/viral_surge_staged.py` on staging; append `docs/LOAD_TEST_RUN_LOG.md`  
5. Do not market above last **SAFE VERIFIED** row without new evidence  
