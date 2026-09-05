# Subscription Analytics Hub — Feature #9

Split into three phases (not one monolithic feature):

## Phase 1: Subscription Lifecycle

**Module:** `bd_platform/subscription_lifecycle.py` + `billing/renewal_alerts.py`

- Built on existing `billing/subscription_engine` SSOT (Stripe webhooks, grace period, sweeper)
- **5-day renewal warning** via `BILLING_RENEWAL_WARNING_DAYS` (in-app alerts + analytics event)
- **Immediate feature cutoff** on expiry via `effective_plan()` + `entitlement_allowed()`
- Audit ledger fan-out → `analytics_events` for all lifecycle transitions

| API | Description |
|-----|-------------|
| `GET /api/platform/subscription-lifecycle/status` | User lifecycle status |
| `POST /api/platform/subscription-lifecycle/upgrade` | Contextual upgrade checkout path |

## Phase 2: Analytics Dashboard

**Module:** `bd_platform/analytics_integrations.py`

- **PostHog optional** — set `POSTHOG_API_KEY` + `POSTHOG_HOST`; events forwarded from `track_subscription_event()`
- **Internal SQLite SSOT** always available (visitors, users, subscribers)
- Not built from scratch — aggregates `platform_analytics` + `billing/admin_metrics`

| API | Description |
|-----|-------------|
| `GET /api/platform/analytics-hub/dashboard` | Admin funnel dashboard |

## Phase 3: Smart Upgrade Recommendations

**Module:** `bd_platform/upgrade_intelligence.py`

- AI-style contextual recommendations from usage signals + tier limits
- Explainable reasons + confidence score + checkout deep-link

| API | Description |
|-----|-------------|
| `GET /api/platform/analytics-hub/upgrade-recommendation` | Personalized upgrade suggestion |

## UI

`/subscription-analytics` — three-tab hub (Lifecycle · Analytics · Smart Upgrade)

## Config

```env
BILLING_RENEWAL_WARNING_DAYS=5
POSTHOG_API_KEY=phc_...
POSTHOG_HOST=https://us.i.posthog.com
```

## Tests

```bash
pytest tests/test_subscription_analytics_hub.py -v
```

## Acceptance

| Criterion | Target | Implementation |
|-----------|--------|----------------|
| Response time | ≤2s | All endpoints track `latency_ms` |
| Accuracy | ≥95% | Upgrade confidence + lifecycle SSOT |
| Uptime | 99% | SQLite fallback when PostHog unavailable |
| Real-time | Instant | Sweeper + webhook-driven updates |

## Related

- `billing/subscription_engine.py` — lifecycle state machine
- `billing/sweeper.py` — expiry + renewal warning scan
- `pricing_catalog.next_upgrade()` — contextual upgrade ladder
- `distribution_compounding.track_subscription_event()` — event bus
