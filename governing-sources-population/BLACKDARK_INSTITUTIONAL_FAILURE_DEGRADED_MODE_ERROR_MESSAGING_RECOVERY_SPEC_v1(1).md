# BLACKDARK Institutional Failure, Degraded Mode, Data Freshness, Error Messaging & Recovery System

**Version:** v1.0  
**Status:** Governing SSOT for implementation  
**Execution intent:** Mandatory source-driven repository audit, reuse, implementation, verification, and engineering closure.

## Institutional final judgment

BLACKDARK MUST NOT implement “error handling” as a collection of isolated messages.

The required system is a five-layer institutional failure architecture:

1. **Failure Classification**
2. **Certainty & Data Quality**
3. **Recovery / Retry / Reconciliation**
4. **User Messaging & Degraded UX**
5. **Observability / Incident / Support Evidence**

This architecture is mandatory because BLACKDARK is a financial intelligence platform where stale, partial, conflicting, indeterminate, or degraded information can be more dangerous than an explicit hard failure.

The governing principle is:

> **The system must tell the user what was affected, to what degree, what is known versus unknown, and what the user can safely do next — without leaking technical internals, fabricating certainty, or presenting degraded data as live.**

## Governing references and standards

Implementation should be reconciled against the latest applicable versions of:
- Nielsen Norman Group usability/error-recovery heuristics
- OWASP Error Handling Cheat Sheet
- OWASP Logging Cheat Sheet
- RFC 9457 Problem Details for HTTP APIs
- Google SRE reliability/graceful degradation/retry principles
- Stripe official error/idempotency/reconciliation practices where applicable to payments
- NIST AI RMF for validity, reliability, transparency, resilience, and abstention logic
- WCAG 2.2 AA
- Existing BLACKDARK Billing, Identity, I18N, Timezone, Audit, Entitlement, and Decision/Evidence architecture

## Non-negotiable governance

- This file is the authoritative Source of Truth for this subsystem.
- Before building, perform `KEEP / REUSE / IMPROVE / REPLACE / BUILD`.
- Reuse existing canonical BLACKDARK owners and do not create duplicate failure, billing, notification, audit, time, or i18n authorities.
- Do not weaken existing tests or security controls.
- Do not fabricate live evidence.
- Do not claim `PASS_LIVE` from local/unit/integration tests alone.
- Every user-facing message must be evidence-backed.
- Every degraded data state must be explicit where it can affect user decisions.
- Any uncertain side-effecting mutation must support an `INDETERMINATE` state rather than a fabricated success/failure result.

---


## ERR-001 — Unified failure state model

BLACKDARK MUST NOT reduce runtime outcomes to only SUCCESS/ERROR.

Canonical user-impact states:
- LOADING
- SUCCESS
- DELAYED
- STALE
- PARTIAL
- DEGRADED
- UNAVAILABLE
- FAILED
- RATE_LIMITED
- AUTH_REQUIRED
- PERMISSION_DENIED
- CONFIRMATION_PENDING
- INDETERMINATE
- RETRYING
- MAINTENANCE
- ABSTAINED

Each state MUST have defined backend semantics, frontend rendering behavior, retry/recovery behavior, observability, and user-facing copy.

---

## ERR-002 — Separate failure class, certainty, and user impact

Every material failure MUST be represented by separate dimensions:
- `failure_class`
- `certainty_state`
- `user_impact`

Example:
`failure_class=PAYMENT_PROVIDER`
`certainty_state=INDETERMINATE`
`user_impact=HIGH`

Do not use one generic status code to represent all three dimensions.

---

## ERR-003 — Unified API problem contract

BLACKDARK SHOULD use RFC 9457-style problem details or a compatible canonical error envelope.

Minimum machine-readable fields:
- `type`
- `title`
- `status`
- `detail`
- `instance`

BLACKDARK extensions:
- `error_code`
- `correlation_id`
- `retryable`
- `retry_after`
- `certainty`
- `data_freshness`
- `affected_component`
- `user_action`

All endpoints MUST converge on one stable error contract instead of ad-hoc JSON shapes.

---

## ERR-004 — Correlation ID / support reference

Every material request/failure MUST receive an opaque correlation identifier.

The identifier MUST propagate through:
- API gateway
- backend
- provider calls
- database operations
- AI pipelines
- notification/email
- billing
- logs/traces

The user does not need to see it on every error. Show a short support reference only when useful:
- severe failures
- repeated failures
- indeterminate transactions
- support-worthy incidents

The identifier MUST NOT embed user ID, email, secrets, internal hostnames, or database IDs.

---

## ERR-005 — Do not expose provider internals unnecessarily

User-facing error text SHOULD describe the affected capability, not the internal vendor.

Preferred:
“خدمة الدفع غير متاحة مؤقتًا.”

Avoid:
“Stripe is down.”

A public status page may identify BLACKDARK components such as Payments, Market Data, AI Intelligence, Notifications, Authentication, Reports, API.

Do not expose vendor topology unless it materially helps the user and is intentionally approved.

---

## ERR-006 — Formal indeterminate outcome state

Any mutation with uncertain outcome MUST support:

- CONFIRMED_SUCCESS
- CONFIRMED_FAILURE
- INDETERMINATE

For `INDETERMINATE`:
- never tell the user it definitely failed
- never tell the user it definitely succeeded
- prevent unsafe duplicate retry
- start reconciliation if possible
- expose clear user guidance

Example:
“استلمنا الطلب لكن لم نتمكن من تأكيد نتيجته بعد. لا تعِد الإرسال الآن. سنتحقق تلقائيًا.”

---

## ERR-007 — Idempotency for sensitive mutations

All duplicate-sensitive mutations MUST support idempotency where technically appropriate.

Priority examples:
- billing/payment mutations
- subscription changes
- account deletion
- paid report generation
- destructive actions
- future transactional workflows

The idempotency mechanism MUST survive retry/reconnect patterns and MUST NOT rely only on client-side button disabling.

---

## ERR-008 — Retry taxonomy

Every error class MUST map to one retry policy:

- SAFE_AUTO_RETRY
- SAFE_USER_RETRY
- DO_NOT_RETRY
- RECONCILE_FIRST

Examples:
SAFE_AUTO_RETRY:
- transient read timeout
- temporary upstream 503 read

SAFE_USER_RETRY:
- failed non-destructive fetch

DO_NOT_RETRY:
- invalid input
- invalid credentials
- permission denied

RECONCILE_FIRST:
- payment mutation
- destructive mutation
- any indeterminate side-effecting request

---

## ERR-009 — Bounded exponential backoff + jitter

Automatic retry MUST use:
- bounded exponential backoff
- jitter
- maximum attempts
- retry budget

Do not hammer a failing dependency and do not create retry storms.

Respect `Retry-After` or provider back-pressure signals when trustworthy.

---

## ERR-010 — Circuit breaker behavior

For repeatedly failing dependencies, implement/reuse a circuit-breaker pattern:

- CLOSED
- OPEN
- HALF_OPEN

While OPEN:
- stop unnecessary calls
- serve safe fallback if available
- expose degraded state to the user
- preserve unaffected product areas

User example:
“هذا الجزء غير متاح مؤقتًا. باقي المنصة يعمل بشكل طبيعي.”

---

## ERR-011 — Canonical data freshness model

All data-sensitive surfaces MUST use a shared freshness contract:

- LIVE
- NEAR_LIVE
- DELAYED
- STALE
- CACHED
- PARTIAL
- UNKNOWN

Evidence fields SHOULD include:
- `source_timestamp`
- `observed_at`
- `ingested_at`
- `last_successful_update`
- `age_seconds`

Never label data LIVE when freshness is unknown.

---

## ERR-012 — Data quality state separate from availability

A working endpoint does not imply trustworthy data.

Canonical quality states:
- COMPLETE
- PARTIAL
- CONFLICTING
- INSUFFICIENT
- SUSPECT
- UNVERIFIED

The UI and decision engine MUST be able to surface degraded quality even when transport/API availability is healthy.

---

## ERR-013 — Decision safety states

BLACKDARK decisions/signals MUST support:

- AVAILABLE
- DEGRADED
- ABSTAINED
- UNAVAILABLE

If evidence is insufficient, stale, materially conflicting, or integrity checks fail, the platform MUST abstain or degrade rather than fabricate confidence or a complete decision.

Example:
“لا توجد أدلة كافية لإصدار قرار موثوق حاليًا.”

---

## ERR-014 — AI failure decomposition

Do not expose internal AI implementation errors such as “LLM timeout”.

Differentiate at least:
- presentation-generation failure
- reasoning/orchestration failure
- evidence/data failure

Examples:
Presentation failure:
“تعذر إنشاء الشرح التحليلي الآن. البيانات الأساسية لا تزال متاحة.”

Evidence failure:
“لا يمكن إصدار تحليل موثوق لأن البيانات المطلوبة غير مكتملة.”

---

## ERR-015 — Graceful partial rendering

A failure in one widget/component MUST NOT automatically crash the entire page.

If 1 of 12 dashboard modules fails:
- render the 11 healthy modules
- isolate the failed module
- show a scoped message
- preserve page navigation and user context

Example:
“هذه الوحدة غير متاحة مؤقتًا.”

---

## ERR-016 — Dependency-aware incident aggregation

If multiple visible components fail due to one shared dependency, do not show duplicate alerts.

Aggregate by incident/dependency where possible.

Example:
“بعض بيانات السوق متأثرة حاليًا.”

Then list affected components only if useful.

---

## ERR-017 — Canonical user action contract

Every user-facing failure MUST map to one explicit action enum:

- NONE
- RETRY
- WAIT
- REFRESH
- SIGN_IN
- VERIFY
- UPDATE_PAYMENT
- CHANGE_INPUT
- CONTACT_SUPPORT
- VIEW_STATUS
- REVIEW_DATA

Frontend behavior and buttons MUST derive from this contract rather than endpoint-specific improvisation.

---

## ERR-018 — Retry button safety

A Retry button MUST NOT be shown if repeating the request can duplicate a side effect.

For indeterminate mutations, prefer:
- CHECK_STATUS
- WAIT
- VIEW_STATUS
- CONTACT_SUPPORT

Example:
Do not show “Retry Payment” after an indeterminate payment.
Show “Check payment status”.

---

## ERR-019 — Internal severity taxonomy

Internal incident severity MUST use a canonical scale such as:

- INFO
- WARNING
- ERROR
- CRITICAL

Do not automatically translate internal severity into alarming user language.

---

## ERR-020 — User-impact taxonomy

Track user impact independently from internal severity:

- NONE
- LOW
- MEDIUM
- HIGH
- CRITICAL

Example:
An upstream provider may trigger an internal ERROR while user impact is LOW because a safe fallback is active.

---

## ERR-021 — Structured internal failure logging

Material failures SHOULD log structured fields such as:

- correlation_id
- canonical UTC timestamp
- component
- operation
- failure_class
- certainty
- severity
- user_impact
- retry_count
- provider/dependency
- latency
- source
- fallback_used
- user_message_key
- resolution/outcome

Logs MUST support diagnosis without leaking secrets.

---

## ERR-022 — Secret and sensitive-data redaction

Never log:
- passwords
- API keys
- OTPs
- session secrets
- access/refresh tokens
- recovery tokens/codes
- raw payment secrets
- private keys
- confidential provider credentials

Sensitive identifiers MUST be redacted or tokenized according to existing BLACKDARK logging policy.

---

## ERR-023 — Observability and service indicators

Failure classes MUST feed observability.

Track where applicable:
- error rate
- success rate
- latency
- retry rate
- fallback rate
- stale-data rate
- partial-data rate
- indeterminate rate
- reconciliation backlog

Use these for SLI/SLO and alerting, not only debugging.

---

## ERR-024 — Componentized status page

BLACKDARK SHOULD support a componentized status model.

Suggested public components:
- Authentication
- Market Data
- Analytics
- AI Intelligence
- Billing
- Notifications
- Reports / Exports
- API

Canonical component states:
- Operational
- Degraded Performance
- Partial Outage
- Major Outage
- Maintenance

---

## ERR-025 — Global incident banner

For broad user-impacting incidents, show one concise global banner.

Example:
“توجد حاليًا مشكلة تؤثر على تحديث بعض بيانات السوق. البيانات الحالية قد تتأخر.”

Provide `View status` when a status surface exists.

Avoid flooding users with multiple toasts for the same incident.

---

## ERR-026 — Maintenance communication

Planned maintenance SHOULD communicate:
- start time
- affected services
- expected behavior (read-only, partial outage, etc.)
- expected return time only when reasonably reliable
- status updates if the window materially changes

Never fabricate an ETA.

---

## ERR-027 — Rate-limit user experience

For rate-limited requests:
- explain that too many requests occurred
- provide retry timing when known
- respect `Retry-After` where applicable
- do not blame the user

Example:
“تم إرسال طلبات كثيرة خلال وقت قصير. حاول مرة أخرى بعد 34 ثانية.”

---

## ERR-028 — Validation errors belong to fields

Input-validation errors SHOULD appear next to the relevant field.

Requirements:
- clear human-readable text
- actionable correction
- accessible association
- preserve valid entered values
- avoid generic global toast when the error is field-specific

---

## ERR-029 — Authentication failure privacy

Authentication failures MUST resist account enumeration.

Example:
“تعذر تسجيل الدخول. تحقق من البيانات أو استخدم استعادة الوصول.”

Do not reveal whether the email, username, or account exists when that disclosure creates enumeration risk.

---

## ERR-030 — Authorization error privacy

Do not expose internal roles, permission names, entitlements, policies, or authorization graph details.

Preferred:
“ليس لديك صلاحية لتنفيذ هذا الإجراء.”

Internal logs may contain the precise authorization denial reason.

---

## ERR-031 — Security-block messaging

Security-driven failures MUST NOT reveal internal risk score, rule IDs, fraud signals, policy thresholds, or bypass hints.

Preferred:
“لا يمكن تنفيذ هذا الإجراء حاليًا لأسباب أمنية.”

Provide a safe recovery/verification path when legitimate.

---

## ERR-032 — Payment error mapping

Do not blindly display raw provider messages.

Normalize provider error codes into BLACKDARK-owned:
- canonical error code
- localized message key
- user action
- retry/reconciliation policy

Use provider decline/error codes for decisioning, but preserve consistent BLACKDARK UX and privacy.

---

## ERR-033 — Centralized localization of error messages

Every user-facing failure message MUST use canonical i18n message keys.

No hard-coded English error strings in user-facing code.

Example keys:
- `error.market_data.delayed`
- `error.payment.indeterminate`
- `error.auth.generic_failure`

Reuse BLACKDARK's existing 38-locale i18n system.

---

## ERR-034 — Accessible error presentation

Error states MUST satisfy accessibility requirements.

Include where appropriate:
- native labels
- `aria-describedby`
- `aria-invalid`
- live regions for dynamic errors
- keyboard-reachable actions
- visible focus
- color not being the only signal

Target WCAG 2.2 AA.

---

## ERR-035 — Prevent error flooding

Repeated identical failures MUST be:
- deduplicated
- aggregated
- rate-limited/cooldown-controlled

Do not display dozens of identical toasts or notifications.

---

## ERR-036 — Offline/network-loss state

Network loss is a first-class state.

Example:
“يبدو أن الاتصال بالإنترنت انقطع. سنعيد الاتصال تلقائيًا.”

If cached content is shown:
“أنت تشاهد آخر بيانات متاحة.”

Do not present cached content as live.

---

## ERR-037 — Cache disclosure

Whenever cache/fallback data is used, expose:
- freshness badge
- last updated time
- source/fallback state where useful

Cached data MUST NOT visually impersonate live data.

---

## ERR-038 — Unknown freshness handling

If data age cannot be established:
- set freshness to UNKNOWN
- do not claim LIVE
- do not invent a timestamp
- expose an appropriate caution state where material

---

## ERR-039 — Evidence quality context for decisions

Decision surfaces SHOULD have machine-readable evidence context such as:
- `evidence_state`
- `source_count`
- `freshness_state`
- `conflict_state`

User-facing decision messages MUST derive from this evidence context.

---

## ERR-040 — Central Error Contract Registry

Create/reuse one canonical registry containing at minimum:

- error_code
- category
- certainty
- severity
- user_impact
- retry_policy
- HTTP status
- message_key
- user_action
- support_reference_policy
- log_level
- alert_policy

Do not allow each endpoint/team to invent incompatible semantics.

---

## ERR-041 — Stable support/API error codes

Stable error codes SHOULD exist for API clients, support, and observability.

Example pattern:
- BD-DATA-STALE
- BD-PAY-IND
- BD-AUTH-001

Codes are not the primary human-facing message.

---

## ERR-042 — Machine-readable API errors

API clients MUST receive a stable machine-readable error schema.

Adopt/reuse RFC 9457-compatible problem details where practical.

Do not return inconsistent `{error}`, `{message}`, `{detail}`, or arbitrary endpoint-specific payloads without a canonical compatibility layer.

---

## ERR-043 — Privacy-safe instance/correlation identifiers

`instance`, request IDs, correlation IDs, and support references MUST be opaque and privacy-safe.

They MUST NOT expose:
- sequential user IDs
- email
- database row IDs
- secrets
- internal hostnames
- provider credentials

---

## ERR-044 — Time and timezone integration

Internal incidents/errors MUST use canonical UTC timestamps.

User-facing timestamps MUST use the resolved user timezone.

Integrate with BLACKDARK's Global Time/Timezone system; do not build a parallel timestamp formatting authority.

---

## ERR-045 — Historical incident integrity

Incident lifecycle changes MUST be append-only/auditable where material.

Suggested states:
- DETECTED
- MITIGATING
- RECOVERING
- RESOLVED

Do not erase historical states merely because the incident is resolved.

---

## ERR-046 — Reconciliation lifecycle

Indeterminate operations MUST support an explicit reconciliation lifecycle where applicable:

- REQUESTED
- PROCESSING
- INDETERMINATE
- RECONCILING
- CONFIRMED_SUCCESS
- CONFIRMED_FAILURE

The user-facing state MUST update when reconciliation resolves the outcome.

---

## ERR-047 — Truthful user messaging

The UI MUST NOT claim system behavior that did not actually occur.

Do not say:
- “تم تسجيل المشكلة” unless a real event/reference was stored
- “نعيد المحاولة تلقائيًا” unless retry is actually scheduled
- “لن يتم خصم شيء” unless evidence supports it
- “سيعود خلال 5 دقائق” without a reliable ETA

User messaging MUST be evidence-backed.

---

## ERR-048 — Support handoff

Support-worthy failures SHOULD provide:
- short support reference
- timestamp
- affected action/component
- safe summary

The user should not need to reconstruct internal technical details manually.

---

## ERR-049 — Help / status / support linkage

Repeated or high-impact errors MAY link to:
- relevant help article
- component status
- support channel

Avoid link overload. Show only the next best action.

---

## ERR-050 — Fault-injection and failure matrix

Engineering verification MUST include fault-injection or equivalent deterministic tests covering:

- timeout
- connection reset
- malformed upstream response
- 4xx
- 429
- 500
- 502
- 503
- 504
- stale data
- partial data
- conflicting data
- database failure
- cache failure
- queue delay
- email failure
- notification failure
- AI failure
- provider failure
- webhook delay
- duplicate retry
- lost response after mutation
- reconciliation
- browser offline/network loss

Tests MUST verify both backend semantics and user-facing behavior where applicable.

---

# Institutional Acceptance Gate

Do not set `PASS_ENGINEERING_FAILURE_SYSTEM=true` unless all locally-buildable requirements ERR-001 → ERR-050 are implemented/reused, integrated, tested, and evidenced.

Required final flags:

```text
FAILURE_STATE_MODEL_PASS=true
FAILURE_CLASS_CERTAINTY_IMPACT_PASS=true
RFC9457_API_ERROR_CONTRACT_PASS=true
CORRELATION_ID_PASS=true
PROVIDER_INTERNALS_PROTECTED_PASS=true
INDETERMINATE_STATE_PASS=true
IDEMPOTENCY_PASS=true
RETRY_TAXONOMY_PASS=true
BACKOFF_JITTER_PASS=true
CIRCUIT_BREAKER_PASS=true

DATA_FRESHNESS_MODEL_PASS=true
DATA_QUALITY_MODEL_PASS=true
DECISION_ABSTENTION_PASS=true
AI_FAILURE_DECOMPOSITION_PASS=true
GRACEFUL_PARTIAL_RENDERING_PASS=true
INCIDENT_AGGREGATION_PASS=true

USER_ACTION_CONTRACT_PASS=true
RETRY_BUTTON_SAFETY_PASS=true
ERROR_SEVERITY_PASS=true
USER_IMPACT_MODEL_PASS=true

STRUCTURED_FAILURE_LOGGING_PASS=true
SECRET_REDACTION_PASS=true
OBSERVABILITY_PASS=true
STATUS_COMPONENT_MODEL_PASS=true
GLOBAL_INCIDENT_BANNER_PASS=true
MAINTENANCE_MESSAGING_PASS=true

RATE_LIMIT_UX_PASS=true
VALIDATION_ERROR_UX_PASS=true
AUTH_ENUMERATION_RESISTANCE_PASS=true
AUTHORIZATION_ERROR_PRIVACY_PASS=true
SECURITY_ERROR_PRIVACY_PASS=true
PAYMENT_ERROR_MAPPING_PASS=true

ERROR_I18N_38_LOCALES_PASS=true
ERROR_ACCESSIBILITY_WCAG_2_2_AA_PASS=true
ERROR_FLOOD_DEDUP_PASS=true
OFFLINE_NETWORK_STATE_PASS=true
CACHE_DISCLOSURE_PASS=true
UNKNOWN_FRESHNESS_PASS=true

DECISION_EVIDENCE_CONTEXT_PASS=true
ERROR_REGISTRY_PASS=true
STABLE_ERROR_CODES_PASS=true
MACHINE_READABLE_API_ERRORS_PASS=true
PRIVACY_SAFE_INSTANCE_IDS_PASS=true

TIMEZONE_ERROR_INTEGRATION_PASS=true
INCIDENT_HISTORY_INTEGRITY_PASS=true
RECONCILIATION_LIFECYCLE_PASS=true
TRUTHFUL_USER_MESSAGING_PASS=true
SUPPORT_HANDOFF_PASS=true
HELP_STATUS_LINKAGE_PASS=true
FAILURE_INJECTION_MATRIX_PASS=true

SOURCE_REQUIREMENTS_ACCOUNTED_FOR=100%
KNOWN_LOCAL_FAILURE_SYSTEM_GAPS=[]
LOCAL_BUILDABLE_FAILURE_SYSTEM_REQUIREMENTS_REMAINING=0
PARTIALLY_IMPLEMENTED_LOCAL_FAILURE_SYSTEM_REQUIREMENTS=0
UNIMPLEMENTED_LOCAL_FAILURE_SYSTEM_REQUIREMENTS=0

PASS_ENGINEERING_FAILURE_SYSTEM=true
PASS_LIVE_NOT_CLAIMED=true
```

# Live Gate

`PASS_LIVE` is separate.

Where applicable, live verification should include:
- real upstream timeout/failure handling
- real stale/partial data presentation
- live correlation/support traceability
- live component/status behavior
- live billing indeterminate/reconciliation behavior
- live email/notification degradation behavior
- live cross-locale error copy
- live timezone rendering of incidents
- live accessibility smoke checks
- live retry/backoff/circuit behavior under controlled conditions

Until actual production-intended evidence exists:

```text
PASS_LIVE_NOT_CLAIMED=true
```

# Cursor Execution Method

Cursor must:

1. Read this file completely before modifying code.
2. Audit the repository exhaustively for all existing error/failure/retry/freshness/degraded/incident logic.
3. Classify every requirement as `KEEP / REUSE / IMPROVE / REPLACE / BUILD`.
4. Reuse existing BLACKDARK canonical systems for:
   - Billing
   - Identity/Auth
   - I18N
   - Timezone
   - Audit
   - Notification/Email
   - Entitlements
   - AI/Decision/Evidence
5. Implement only the missing or deficient delta.
6. Add source-driven tests for each requirement.
7. Perform a second full source pass after implementation.
8. Perform duplicate/canonical ownership checks.
9. Run targeted local tests first, then relevant regression once local green is achieved.
10. Produce a final institutional closure report with:
   - branch
   - final material SHA
   - spec SHA256
   - requirement count
   - KEEP/REUSE/IMPROVE/REPLACE/BUILD counts
   - local complete count
   - live/external gated count
   - remaining local count
   - implementation paths
   - tests/results
   - failure-state model
   - freshness/quality model
   - retry/idempotency/reconciliation model
   - user messaging model
   - error registry
   - API error contract
   - status/incident model
   - i18n/accessibility result
   - observability/logging result
   - duplicate/ownership scan
   - second source pass
   - all final acceptance flags
   - exact remaining live gates

Institutional completion wording:

> **All defined locally-buildable failure, degraded-mode, data-freshness, error-messaging, recovery, reconciliation, and observability requirements passed under the tested scope, and no known local material gaps remain.**

Do NOT use:
- “100% bug free”
- “perfect”
- “PASS_LIVE”

unless actual production evidence supports the specific claim.
