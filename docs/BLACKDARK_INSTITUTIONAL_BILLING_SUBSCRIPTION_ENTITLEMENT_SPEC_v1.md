# BLACKDARK Institutional Billing, Subscription & Entitlement Specification

**Version:** Final Consolidated & Reconciled v1.0  
**Status:** Proposed Governing SSOT for implementation  
**Purpose:** المرجع الحاكم الوحيد لبناء ومراجعة واختبار نظام الاشتراكات والفوترة والصلاحيات في BLACKDARK.

## قواعد الحوكمة

- هذا الملف هو **Source of Truth** لمتطلبات نظام الاشتراكات.
- الـLedger أداة تتبع فقط، ولا يجوز أن يختصر أو يلغي أي Requirement في هذا الملف.
- قبل أي بناء: Audit/Re-use وفق `KEEP / REUSE / IMPROVE / REPLACE / BUILD`.
- كل Requirement له ID ثابت من `BILL-001` إلى `BILL-062`.
- لا `PASS_ENGINEERING` إلا بعد إغلاق `BILL-060`.
- لا `PASS_LIVE` إلا بعد إغلاق `BILL-061`.
- لا يجوز خلط نجاح الاختبارات المحلية مع الجاهزية الحية أو الاعتماد الخارجي.

---

## BILL-001 — المبادئ غير القابلة للتفاوض

1. Billing State ≠ Entitlement State.
2. لا يتم منح Paid Entitlement جديد إلا بعد دليل دفع موثوق صالح.
3. `customer.subscription.updated` وحده لا يكفي لفتح مستوى أعلى.
4. `past_due` وحده لا يؤدي تلقائيًا إلى سحب كل الصلاحيات.
5. entitlement مدفوع ومثبت يظل صالحًا حتى `paid_through` وفق policy.
6. أي entitlement جديد أو غير موثق = Fail-Closed.
7. Free Plan داخلي بالكامل، بدون Stripe Subscription وبدون بطاقة.
8. Stripe لا يصبح SSOT مباشر لصلاحيات المنتج.
9. Webhooks لا تُطبق مباشرة على حساب المستخدم.
10. كل Webhook يُخزن أولًا في Durable Inbox.
11. Idempotency إلزامية على مستوى قاعدة البيانات.
12. Out-of-order protection إلزامي.
13. Reconciliation مع Stripe إلزامي.
14. كل financial calculation يستخدم Decimal أو minor units، وليس float.
15. كل state transition له Audit Trail.
16. كل override يدوي حساس له reason + authorization + audit.
17. لا ادعاء PCI/SOC2/ISO certification بدون الإثبات الخارجي الفعلي.
18. لا تخزين PAN/CVC في BLACKDARK.
19. لا client-side payment success يفتح entitlement.
20. لا silent financial corrections.

---


## BILL-002 — Provider Eligibility Gate — قبل Live

قبل تشغيل مدفوعات Production يجب التحقق من: دولة الكيان القانوني، أهلية Stripe account، بنك وعملة التسوية، وسائل الدفع المتاحة، merchant pricing، tax residency/registrations، وB2B/B2C jurisdictions.

الحالة الحاكمة قبل التحقق:
`PRODUCTION_PAYMENT_PROVIDER_ELIGIBILITY = BLOCKED_UNTIL_VERIFIED`

تغيير أهلية المزود لاحقًا يغيّر هذا الـgate فقط ولا يعيد تصميم النظام.

---


## BILL-003 — المعمارية الحاكمة

المسار الحاكم الوحيد:
User → Checkout / Customer Portal → Stripe Billing / Payments → Signed Webhook Endpoint → Durable Billing Event Inbox → Signature Verification → Schema Validation → DB-Level Event Deduplication → Out-of-Order / Version Guard → Transactional Event Processor → Canonical Billing Projection → Entitlement Decision Engine → Capability Enforcement Layer → Audit Ledger → Metrics / Alerts.

Reconciliation Worker يقارن دوريًا:
Stripe ↔ Billing Projection ↔ Entitlement Ledger.

ممنوع:
- Stripe webhook → مباشرة User Tier.
- Stripe API status → permission check per request.

---


## BILL-004 — قاعدة البيانات

Production: PostgreSQL.
SQLite: Local / test / development only.

متطلبات الإنتاج: ACID، concurrency، row locking، unique constraints، transactional updates، recovery، durable inbox، reconciliation، audit history.

---


## BILL-005 — Billing Event Inbox

كل Stripe event يُحفظ قبل المعالجة.
الحد الأدنى: stripe_event_id, event_type, object_id, stripe_created_at, received_at, payload_hash, processing_status, attempt_count, processed_at, last_error, last_attempt_at.
قيد إلزامي: `UNIQUE(stripe_event_id)`.

---


## BILL-006 — Webhook Security

إلزامي: signature verification، raw request body validation، timestamp tolerance، replay protection، secret rotation، separate test/live webhook secrets، log redaction، ورفض event غير موثق. Retry policy الداخلية configurable.

---


## BILL-007 — Async Processing

Webhook endpoint: verify → persist → ACK بسرعة → process async. ممنوع العمليات الطويلة قبل acknowledgement.

---


## BILL-008 — Out-of-Order Protection

حفظ ومقارنة event_created_at, object_id, billing_generation/version, last_applied_event_id, last_applied_event_created_at. حدث أقدم لا يعمل rollback لحالة أحدث بدون reconciliation rule صريحة.

---


## BILL-009 — Billing State Model

يشمل على الأقل: FREE, CHECKOUT_PENDING, INCOMPLETE, INCOMPLETE_EXPIRED, TRIALING, ACTIVE, PAST_DUE, UNPAID, PAUSED, CANCEL_AT_PERIOD_END, CANCELED, REFUND_PENDING, PARTIALLY_REFUNDED, REFUNDED, DISPUTE_OPEN, DISPUTE_WON, DISPUTE_LOST. لا يتم نسخ Stripe status حرفيًا؛ يبنى canonical internal billing projection.

---


## BILL-010 — Entitlement State Model

مستقل عن Billing ويشمل على الأقل: FREE, PAID_PENDING, PAID_ACTIVE, PAID_RECOVERY, PAID_CANCELING_AT_PERIOD_END, SUSPENDED, REVOKED, MANUAL_TEMPORARY_OVERRIDE.
القرار يعتمد على verified payment proof, paid_through, billing state, tier, price version, recovery policy, refund/dispute state, manual override.

---


## BILL-011 — Paid-Through Semantics

كل entitlement مدفوع يسجل effective_from, paid_through, tier, payment_reference, subscription_reference, verification_source.
عند Stripe outage: لا grant جديد غير موثق، ولا revoke لحق مدفوع مثبت داخل paid_through لمجرد outage.

---


## BILL-012 — Free Plan

Free بدون بطاقة وبدون Stripe Subscription؛ entitlement داخلي، والترقية إلى Paid عبر Checkout.

---


## BILL-013 — Product / Price Registry

Registry واحدة: FREE, PRO, ELITE, QUANT, INSTITUTIONAL.
كل record: tier_id, stripe_product_id, stripe_price_id, currency, billing_interval, amount_minor, price_version, effective_from, effective_to, grandfathering_policy, tax_behavior, entitlement_profile, active.
ممنوع scattering للـPrice IDs.

---


## BILL-014 — Price Versioning

دعم price_version, grandfathered, effective_from, migration_policy. أي تغيير سعر لا يغيّر عقود المستخدمين الحاليين بلا قصد.

---


## BILL-015 — Signup

Free: Account → entitlement FREE.
Paid: Account → Checkout → verified payment → Billing Projection → Entitlement.
لا client redirect ولا success page تعتبر payment proof.

---


## BILL-016 — Upgrade

Upgrade request → calculate policy/proration → Stripe mutation → required payment confirmation → verified payment success → billing transaction → entitlement upgrade → audit.
إذا الدفع فشل: لا فتح للمستوى الأعلى.

---


## BILL-017 — Downgrade

Default: effective at end of current paid period. المستخدم يرى تاريخ نهاية الحالي وبداية الجديد. Immediate downgrade فقط بسياسة صريحة.

---


## BILL-018 — Proration

السياسة تحدد صراحة: upgrade_proration, downgrade_proration, invoice_now, defer_to_next_invoice, credit_behavior. لا نفترض خصمًا فوريًا دائمًا.

---


## BILL-019 — Renewal

Stripe Billing يدير recurring invoice/payment attempts. تكلفة Billing الفعلية تدخل Cost Model ولا يوصف بأنه مجاني.

---


## BILL-020 — Renewal Reminder

سياسة BLACKDARK: تذكير قبل التجديد بـ5 أيام. السجل: renewal_at, estimated_subtotal, estimated_tax, estimated_total, currency, tier, notice_sent_at, delivery_status.

---


## BILL-021 — Payment Failure / Dunning

`past_due` يدخل Recovery. القرار يعتمد على decline category, paid_through, retry policy, billing state, grace policy. لا revoke أعمى عند أول failure. Retry policy configurable.

---


## BILL-022 — Grace Period

Configuration حاكمة: grace_enabled, grace_duration, eligible_failure_categories, hard_failure_behavior, access_during_grace, final_revoke_condition.
التوصية: الحق المثبت يستمر حتى paid_through، ثم recovery/grace حسب policy؛ hard cancellation/unpaid يؤدي إلى revoke وفق transition موثق.

---


## BILL-023 — Card Declines

UI mapping مثل expired_card, incorrect_number, incorrect_cvc, insufficient_funds, generic_decline, authentication_required، مع generic fallback وعدم كشف تفاصيل داخلية غير مناسبة.

---


## BILL-024 — Payment Methods

حيث يسمح الحساب والبلد: Cards, Apple Pay, Google Pay, Link, ACH, SEPA, Local payment methods. لا تستخدم عبارة مجانية؛ availability/pricing تختلف.

---


## BILL-025 — Customer Portal

حسب policy: update payment method, invoices, cancellation, downgrade, upgrade إن سمح، billing address, tax details. إعدادات Portal version-controlled/auditable.

---


## BILL-026 — Cancellation

دعم CANCEL_NOW وCANCEL_AT_PERIOD_END. Self-service واضح وبدون dark patterns.

---


## BILL-027 — Refunds — P0 Core

دعم FULL_REFUND وPARTIAL_REFUND مع Stripe reference، invoice/credit effect، entitlement effect، duplicate protection، audit، reconciliation.

---


## BILL-028 — Disputes / Chargebacks — P0 Core

States: DISPUTE_OPEN, DISPUTE_WON, DISPUTE_LOST. لكل حالة entitlement policy صريحة. لا hard-code network threshold واحد. يمكن استخدام هدف داخلي `<0.5%` للتنبيه فقط.

---


## BILL-029 — Reconciliation Worker

يقارن Stripe truth ↔ Billing Projection ↔ Entitlement Ledger. الناتج MATCH/MISMATCH/UNKNOWN. أي mismatch يولد alert/evidence ولا يُصحح ماليًا بصمت.

---


## BILL-030 — Invoice Handling

تسجيل invoice_id, invoice_status, subtotal, tax, discount, total, currency, period, paid_at, payment_reference، مع download من Portal حيث متاح.

---


## BILL-031 — Financial Arithmetic

ممنوع float. استخدم Decimal أو integer minor units. دعم rounding rules, zero-decimal currencies, refund/tax/proration rounding.

---


## BILL-032 — Cost Model

`SUBSCRIPTION_COST_MODEL` لا يعتمد نسبًا عالمية ثابتة. Inputs: merchant_country, payment_method, customer_country, card_origin, currency, fx_required, billing_product, tax_product, fraud_product, dispute_cost. الأسعار من configuration حديث ومصدر موثوق.

---


## BILL-033 — Taxes

Tax profile: merchant_jurisdiction, customer_location, B2C/B2B, tax_id, VAT_id, registration_status, tax_exemption, reverse_charge, tax_behavior, invoice_tax_evidence. تفعيل Stripe Tax لا يساوي تلقائيًا اكتمال الالتزام القانوني.

---


## BILL-034 — SCA / 3DS

عند انطباق PSD2/SCA: PaymentIntent/SetupIntent flow مناسب، 3DS عند الحاجة، no bypass، وعدم منح entitlement في failure/pending غير الموثق.

---


## BILL-035 — PCI

المرجع: PCI DSS v4.0.1. BLACKDARK لا يخزن PAN/CVC، يستخدم Stripe-hosted/tokenized collection، يقلل PCI scope، ولا يدعي PCI Level 1 لمجرد استخدام Stripe.

---


## BILL-036 — Secrets

separate test/live secrets، restricted keys حيث ينطبق، least privilege، secret rotation، webhook-secret rotation، no secrets in repo/logs، audit access.

---


## BILL-037 — Audit Trail

كل transition يسجل audit_id, timestamp, actor_type, actor_id, event_source, event_id, old_state, new_state, reason, billing_reference, entitlement_reference, correlation_id.

---


## BILL-038 — Break-Glass

أي manual entitlement override يسجل actor, role, reason, ticket, old_state, new_state, created_at, expires_at, approval_actor. High-risk paid override يتطلب dual approval. لا يغير financial history.

---


## BILL-039 — Admin Billing Console

وظائف: subscriptions, event inbox, billing projection, entitlement state, reconciliation, refund workflow, dispute status, audit log, diagnostics. ممنوع uncontrolled manual tier granting.

---


## BILL-040 — Fraud / Abuse

P0: Radar configuration، card testing controls، repeated decline throttling، velocity limits، account/trial abuse، coupon abuse، suspicious upgrade/refund loops. لا تعامل الأسعار والخصائص كأرقام عالمية ثابتة.

---


## BILL-041 — Observability

P0 metrics: payment success/failure, webhook signature failures, processing success/latency/backlog, DLQ_size, reconciliation mismatch, paid_without_entitlement, entitlement_without_payment_proof, refund failures, disputes, invoice failures, tax failures.

---


## BILL-042 — Alerts

Critical alerts: invalid webhook spike, inbox backlog, DLQ growth, payment/no entitlement, entitlement/no billing proof, reconciliation mismatch, high decline velocity, dispute spike, invoice failures, tax failure.

---


## BILL-043 — B2B / Institutional Architecture

البنية تدعم منذ البداية organization_id, billing_owner/admin, members, seat_count/entitlement, contract_id, custom_price, payment_terms, invoice_billing, PO_reference, tax_id, custom_entitlement_profile, contract_start/end.

---


## BILL-044 — Seat Enforcement

Server-side enforcement: paid seats vs active entitled members. ممنوع الاعتماد على UI فقط.

---


## BILL-045 — Enterprise Payment Terms

P1 تنفيذ كامل، لكن architecture تستوعب NET_15, NET_30, invoice_due, purchase_order, manual settlement evidence, contract entitlement.

---


## BILL-046 — Multi-Currency

لا يطلق افتراضيًا بدون business decision. Architecture جاهزة. عند التفعيل: price_per_currency, currency-specific rounding, invoice/refund currency, FX policy, tax behavior.

---


## BILL-047 — Legal Compliance Layer

ملف حاكم: `docs/SUBSCRIPTION_LEGAL_BASIS.md`.
US: ROSCA, FTC Act, applicable state ARL laws, card-network rules.
EEA: PSD2/SCA, GDPR, applicable consumer rules.
باقي الدول: local review حسب الأسواق الفعلية.
لا يوجد قانون عالمي واحد للاشتراكات.

---


## BILL-048 — Consent Evidence

تسجيل terms_version, renewal_disclosure_version, consent_at, consent_source, user/account_id, price/tier, billing_frequency. لا يلزم consent جديد لكل recurring charge الطبيعي، لكن initial consent وشروط التجديد يجب توثيقها حسب القانون.

---


## BILL-049 — Data Privacy

Payment data ليست تلقائيًا GDPR Article 9 special category. يطبق data minimization, lawful basis, retention schedule, access controls, deletion subject to legal retention obligations, financial retention where required.

---


## BILL-050 — Retention

نفصل product personal data deletion، payment-method removal، subscription cancellation، وlegally required invoice/tax/accounting retention. لا حذف شامل وفوري لكل شيء.

---


## BILL-051 — Customer UX

قبل الشراء: price, currency, billing interval, automatic renewal, tax, discount, total, cancellation terms. لا dark patterns.

---


## BILL-052 — Capability Enforcement

كل tier مرتبط بـ `entitlement_profile_version`. Capability enforcement server-side. لا client/UI-only gating.

---


## BILL-053 — Subscription-to-Capability Consistency

اختبار إلزامي: FREE→Free only، PRO→PRO allowed، ELITE→ELITE allowed، QUANT→QUANT allowed، INSTITUTIONAL→negotiated profile.

---


## BILL-054 — Failure Safety

اختبارات إلزامية لـStripe outage, DB outage, queue outage, duplicate/delayed/old/malformed event, processing crash, reconciliation mismatch.

---


## BILL-055 — Dead Letter Queue

الأحداث التي تفشل بعد configured attempts تنتقل DLQ وتحفظ event ID, reason, payload reference, attempts, timestamps, replay status.

---


## BILL-056 — Replay

Manual/admin replay يكون permission-controlled, idempotent, auditable, ولا يسبب duplicate financial effect.

---


## BILL-057 — Concurrency

اختبار: upgrade+cancellation معًا، two workers same event، two events same subscription، refund أثناء downgrade pending، dispute أثناء renewal.

---


## BILL-058 — Reliability

كل mutation deterministic، idempotent حيث ينطبق، transaction-safe، retry-safe.

---


## BILL-059 — Core P0 Test Matrix

قبل launch: Free/Paid signup، checkout success/failure، card declines، SCA، incomplete payment، renewal success/failure، recovery، past_due/unpaid/canceled، cancel now/period-end، upgrade success/failure، downgrade، proration، duplicate/invalid/out-of-order webhooks، replay، processor crash، Stripe/DB outage، concurrency، refunds، disputes، reconciliation mismatch، invoice، tax success/failure، Portal update، Price version migration، entitlement mismatch، seat enforcement where enabled.

---


## BILL-060 — Acceptance Gates

لا `PASS_ENGINEERING` إلا بعد:
PAYMENT_PROVIDER_ARCHITECTURE_COMPLETE=true
BILLING_STATE_MACHINE_COMPLETE=true
ENTITLEMENT_STATE_MACHINE_COMPLETE=true
DURABLE_EVENT_INBOX_COMPLETE=true
DB_IDEMPOTENCY_COMPLETE=true
OUT_OF_ORDER_PROTECTION_COMPLETE=true
PRODUCT_PRICE_REGISTRY_COMPLETE=true
UPGRADE_PAYMENT_PROOF_GATE=true
RECONCILIATION_COMPLETE=true
REFUND_CORE_COMPLETE=true
DISPUTE_CORE_COMPLETE=true
AUDIT_TRAIL_COMPLETE=true
BREAK_GLASS_CONTROL_COMPLETE=true
SECURITY_CONTROLS_COMPLETE=true
P0_OBSERVABILITY_COMPLETE=true
P0_TEST_MATRIX_GREEN=true
KNOWN_LOCAL_MATERIAL_GAPS=[]

---


## BILL-061 — Live Activation Gate

مستقل عن Engineering:
PROVIDER_ELIGIBILITY_VERIFIED
LIVE_STRIPE_ACCOUNT_READY
LIVE_KEYS_CONFIGURED
LIVE_WEBHOOK_REGISTERED
LIVE_PAYMENT_METHODS_VERIFIED
LIVE_TAX_CONFIGURATION_VERIFIED
LIVE_SCA_PATH_VERIFIED
LIVE_CHECKOUT_SMOKE_PASS
LIVE_RENEWAL_EVIDENCE
LIVE_REFUND_EVIDENCE
LIVE_RECONCILIATION_PASS

حتى وقتها: `PASS_LIVE_NOT_CLAIMED=true`.

---


## BILL-062 — مراحل التنفيذ النهائية

Phase 0 — Audit & Reuse: KEEP / REUSE / IMPROVE / REPLACE / BUILD على النظام الموجود.
Phase 1 — P0 Financial Core: PostgreSQL, Inbox, event processing, billing state, entitlement, price registry, audit.
Phase 2 — Stripe Flows: Checkout, renewal, Portal, upgrade, downgrade, cancellation, dunning.
Phase 3 — Financial Correctness: reconciliation, refunds, disputes, proration, taxes, invoices.
Phase 4 — Protection & Operations: Radar/fraud, SCA, observability, alerts, break-glass, security.
Phase 5 — P0 Verification: test matrix, regression, security, billing/entitlement correctness.
Phase 6 — P1 Expansion: advanced B2B, seats UI, enterprise invoice ops, advanced admin, multi-currency, analytics.
Phase 7 — Live Activation: فقط بعد Provider Eligibility.

---
