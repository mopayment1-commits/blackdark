# SPEC_03 Runtime Truth Table

| Req ID | Section | Status | Evidence |
|--------|---------|--------|----------|
| REQ-S03-001 | §3 | **YES** | billing != entitlement; no webhook→tier shortcut |
| REQ-S03-002 | §2 | **YES** | canonical tiers ('free', 'pro', 'elite', 'quant', 'institutional') |
| REQ-S03-003 | §4 | **YES** | missing user resolves to FREE entitlement |
| REQ-S03-004 | §5 | **YES** | redirect + client tier=pro blocked without subscription |
| REQ-S03-005 | §6 | **YES** | signed + idempotent webhook pipeline referenced |
| REQ-S03-006 | §7 | **YES** | BillingState enum in billing_entitlement_common |
| REQ-S03-007 | §8 | **YES** | EntitlementState enum in billing_entitlement_common |
| REQ-S03-008 | §9 | **YES** | effective_plan + paid_through in subscription_engine |
| REQ-S03-009 | §10 | **YES** | canonical tiers ('free', 'pro', 'elite', 'quant', 'institutional') |
| REQ-S03-010 | §22, §24 | **YES** | signed + idempotent webhook pipeline referenced |
| REQ-S03-011 | §23 | **YES** | stripe Webhook.construct_event in dashboard.py + IV probe |
| REQ-S03-012 | §25 | **YES** | out_of_order_provider_event_created |
| REQ-S03-013 | §26 | **YES** | minor units only |
| REQ-S03-014 | §27 | **YES** | verified pro allowed; unverified capped |
| REQ-S03-015 | §28 | **YES** | LAUNCH57_IDS only; parked not sellable |
| REQ-S03-016 | §29 | **YES** | _TIER_VARIABLES separate from capability IDs |
| REQ-S03-017 | §31 | **YES** | unverified_paid_tier_claim |
| REQ-S03-018 | §21 | **YES** | reconciliation fail-closed on uncertain grant |
| REQ-S03-019 | §16 | **YES** | payment_failed sets grace_period_end in subscription_engine |
| REQ-S03-020 | §18 | **YES** | schedule_cancel_at_period_end tested in subscription_engine tests |
| REQ-S03-021 | §37 | **YES** | financial_security_common PCI references |
| REQ-S03-022 | §38 | **YES** | record_audit in subscription_engine activate_checkout |
| REQ-S03-023 | §5, §27 | **YES** | redirect + client tier=pro blocked without subscription |
| REQ-S03-024 | §45 | **YES** | IV in independent_verification() |
| REQ-S03-025 | §46 | **YES** | PASS_LIVE=false; LIVE_VALIDATION_PENDING=true |
| REQ-S03-026 | §49 | **YES** | 22 AC flags; key subset pass |
