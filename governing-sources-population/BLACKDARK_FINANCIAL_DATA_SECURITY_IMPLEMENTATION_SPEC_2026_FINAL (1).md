# BLACKDARK FINANCIAL DATA SECURITY IMPLEMENTATION SPEC — 2026 FINAL

**Status:** FINAL / IMPLEMENTATION-GOVERNING  
**Project:** BLACKDARK  
**Scope:** Protection of user financial data, payment data, banking data, financial credentials, tokens, secrets, and related privileged access  
**Execution Standard:** Institutional / Production / Acquisition-Ready  
**Core Principle:** Financial Data Minimization + Non-Custody by Design

---

# 1. Governing Security Principles

1. BLACKDARK SHALL NOT intentionally receive, process, store, log, cache, back up, index, analyze, or expose raw card PAN, CVV/CVC, PIN, magnetic-stripe/track data, or equivalent sensitive authentication data where provider-hosted/tokenized collection is available.
2. Payment-card data collection SHALL use provider-hosted/tokenized flows only, such as Stripe Checkout, Stripe Elements, or equivalent approved components.
3. BLACKDARK SHALL store only the minimum payment references required for operation, such as:
   - Customer ID
   - Payment Method ID
   - Subscription ID
   - Payment Intent ID where needed
   - Tokenized references
   - Card brand / last4 / expiry only when operationally required
4. Sensitive financial and banking data SHALL be classified, minimized, encrypted, access-controlled, monitored, and deleted according to documented retention rules.
5. Administrative and privileged access touching financial data or financial secrets SHALL require strong MFA, least privilege, and complete auditability.
6. Cryptographic keys SHALL be managed centrally through approved KMS/HSM/secret-management services.
7. New institutional cryptographic paths SHOULD target FIPS 140-3 validated modules where applicable.
8. Discovery of PAN/CVV/SAD, exposed financial credentials, unauthorized financial export, or equivalent sensitive-data leakage SHALL be treated as a security incident, not an ordinary defect.
9. No control SHALL be marked COMPLETE solely because code exists. Closure requires machine-verifiable evidence.

---

# 2. Mandatory Data Classification

BLACKDARK SHALL implement and document the following minimum financial-data classes:

## FDS-C1 — Restricted Payment Authentication Data
Examples:
- CVV/CVC
- PIN
- full track data
- magnetic stripe data
- equivalent sensitive authentication data

Policy:
- NEVER STORE
- NEVER LOG
- NEVER CACHE
- NEVER BACK UP
- NEVER SEND TO ANALYTICS/AI/LLM
- NEVER RETAIN AFTER AUTHORIZATION

## FDS-C2 — Restricted Card Data
Examples:
- Full PAN

Policy:
- MUST NOT enter BLACKDARK backend where provider-hosted/tokenized collection is available.
- MUST NOT appear in logs, traces, tickets, analytics, exports, backups, or support tooling.

## FDS-C3 — Restricted Banking Data
Examples:
- Full bank account numbers
- Routing numbers
- Equivalent bank-payment credentials

Policy:
- Provider-hosted/tokenized collection preferred.
- Store only tokenized references unless explicit documented business necessity requires otherwise.

## FDS-C4 — Financial Credentials and Secrets
Examples:
- Stripe secret keys
- Webhook signing secrets
- Banking provider credentials
- Exchange API secrets
- OAuth refresh tokens
- Private integration credentials

Policy:
- Secret Manager/KMS/HSM only.
- No plaintext database storage.
- No source-code storage.
- No client-side exposure.
- No logging.

## FDS-C5 — Sensitive Financial Data
Examples:
- balances
- transactions
- ownership data
- financial account metadata
- user financial intelligence

Policy:
- Need-to-know access only.
- Strong authorization.
- Encryption at rest.
- Explicit retention period.
- Audit trail.

## FDS-C6 — Payment References
Examples:
- Stripe Customer ID
- PaymentMethod ID
- Subscription ID
- tokenized bank/payment references

Policy:
- Allowed only when operationally necessary.
- Protected as sensitive application data.

---

# 3. Payment Architecture — Mandatory

The intended architecture SHALL be:

User Browser / Client  
→ Stripe-hosted or approved provider-hosted payment component  
→ Payment Provider

NOT:

User Browser / Client  
→ BLACKDARK Backend receiving PAN/CVV  
→ Payment Provider

Mandatory controls:

- Stripe Checkout / Elements or equivalent approved provider-hosted/tokenized flow only.
- No custom card form that submits raw PAN/CVV to BLACKDARK backend.
- No server endpoint accepting raw PAN/CVV.
- No PAN/CVV in:
  - HTTP request logs
  - application logs
  - error logs
  - APM
  - traces
  - analytics
  - session replay
  - support tickets
  - screenshots
  - data warehouse
  - object storage
  - backups
  - CI artifacts
- Periodic automated scanning SHALL verify that PAN/CVV is absent.

---

# 4. Banking Data Architecture

Where financial-account linking is introduced:

- Prefer provider-hosted/tokenized collection.
- BLACKDARK SHALL NOT collect full bank credentials manually if tokenized provider flows are available.
- Request only minimum permissions necessary.
- Default financial-account permission = DENY.
- Permission classes such as balances, transactions, ownership, payment_method, or equivalent SHALL be requested only when the capability explicitly requires them.
- Production banking credentials SHALL never be reused in development or staging.

---

# 5. Secrets and Financial Credential Vault

All financial secrets SHALL be stored outside application code and plaintext databases.

Mandatory controls:

- Central Secret Manager.
- KMS/HSM-backed encryption where appropriate.
- No committed .env secrets.
- No plaintext secrets in configuration files.
- No secrets in application logs.
- No secrets in browser-delivered JavaScript.
- Environment-specific credentials:
  - Production
  - Staging
  - Development
- Production secrets MUST differ from non-production secrets.
- Secret access SHALL be IAM-controlled.
- Secret access SHALL be audited.
- Rotation procedure SHALL exist.
- Webhook secrets and API credentials SHALL support revocation and rotation.
- Prefer short-lived credentials wherever supported.

---

# 6. Cryptographic Controls

## In Transit
- TLS 1.2 minimum.
- TLS 1.3 preferred where supported.
- HTTPS-only.
- Secure cookies.
- HSTS.
- No insecure downgrade/fallback.

## At Rest
Sensitive financial data SHALL use approved encryption at rest.

Preferred design:
- Envelope encryption
- DEK for data encryption
- KEK protected by centralized KMS/HSM
- No decryption key stored beside encrypted data

## FIPS
For new institutional cryptographic paths where regulatory/institutional assurance applies:
- Prefer/require FIPS 140-3 validated cryptographic modules.
- Validation evidence must identify the actual module/configuration used.
- “FIPS compatible” or marketing-only statements are insufficient evidence.

---

# 7. Authentication and Privileged Access

Mandatory:

- MFA for all privileged/admin access touching financial data, financial secrets, production billing, payment configuration, or banking integrations.
- Prefer phishing-resistant MFA:
  - FIDO2
  - WebAuthn
  - Passkeys
  - Hardware security keys for highest privilege
- No shared admin accounts.
- Named privileged identities only.
- Short-lived privileged sessions where possible.
- Least privilege.
- RBAC and/or ABAC as appropriate.
- No permanent broad database permissions without documented justification.

---

# 8. Step-Up Authentication

Step-Up authentication SHALL be required for high-risk actions including:

- change payment method
- add/change linked financial account
- export financial data
- bulk export
- reveal highly sensitive financial information
- change MFA
- create or rotate financial API credentials
- create privileged API keys
- modify admin permissions
- change billing ownership
- support impersonation
- break-glass access
- other equivalent high-risk financial operations

---

# 9. Fine-Grained Authorization

Authorization SHALL be resource-aware.

Access decisions SHOULD evaluate:

- Subject identity
- Resource
- Action
- Ownership/tenant
- Current privilege
- Authentication strength
- Session freshness
- Context
- Risk
- Policy result

Authentication alone SHALL NOT imply authorization.

Broad patterns such as:

logged_in = allow

or

is_admin = allow_all

are NOT sufficient for sensitive financial operations.

---

# 10. Financial Data Segmentation

Logical/security separation SHALL exist between at least:

- Authentication
- Payment references
- Billing
- Banking integrations
- User financial intelligence
- Exchange/API credentials
- Audit data
- Analytics
- Support tooling
- AI/LLM pipelines

Analytics, support, search, AI, and LLM systems SHALL NOT receive sensitive financial credentials or restricted payment data by default.

---

# 11. AI / LLM / Model Safety Boundary

The following SHALL NEVER be sent to:

- LLM prompts
- model training datasets
- fine-tuning datasets
- embeddings
- vector databases
- AI telemetry
- external AI providers

Data prohibited:
- PAN
- CVV/CVC
- PIN
- bank credentials
- payment secrets
- API secrets
- refresh tokens
- private keys
- equivalent restricted authentication data

Any AI-accessible financial dataset SHALL be minimized, sanitized, authorized, and policy-controlled.

---

# 12. Audit Logging

For sensitive financial operations, logs SHALL capture:

- actor / service identity
- action
- resource
- timestamp
- tenant/account context where applicable
- authentication strength
- authorization/policy decision
- result
- source/context where appropriate
- correlation/request ID

Audit logs SHALL NOT contain the protected secret or restricted financial value itself.

Security audit logs SHOULD be:

- append-oriented
- tamper-evident
- access-restricted
- integrity-verifiable
- time-synchronized
- separately retained where appropriate

Attempts to disable or bypass auditing SHALL generate alerts.

---

# 13. Detection, DLP, and Secret Scanning

Automated detection SHALL scan appropriate repositories and data paths for:

- PAN-like patterns
- CVV-like accidental fields
- bank-account patterns where applicable
- API secrets
- private keys
- access tokens
- payment-provider secrets
- webhook secrets

Coverage SHOULD include:

- source repository
- CI/CD artifacts
- application logs
- object storage
- databases where scanning is safe and appropriate
- support exports
- data exports
- configuration repositories

At minimum:
- pre-commit or repository secret scanning
- CI secret scanning
- runtime/log scanning
- periodic verification scans

Confirmed sensitive-data detection SHALL trigger an incident workflow.

---

# 14. Webhook Security

Financial/payment webhooks SHALL implement:

- TLS
- provider signature verification
- invalid-signature rejection
- replay protection
- timestamp validation where supported
- idempotency
- duplicate-event handling
- minimal payload retention
- sanitized error handling
- audit trail
- safe dead-letter/retry behavior
- no secret leakage

---

# 15. Environment Isolation

Production, staging, and development SHALL be separate trust boundaries.

Mandatory:

- No production secrets in development.
- No production secrets in staging unless explicitly justified by a controlled test architecture.
- No raw production financial data copied into dev/test by default.
- Test datasets SHALL be synthetic, anonymized, or tokenized.
- Developers SHALL NOT have permanent broad production DB access.
- Production access SHALL be individually authorized and audited.

---

# 16. Service and Machine Identities

Each service, worker, job, integration, and automation SHALL use a distinct identity where technically practical.

Mandatory:

- unique service identity
- scoped permissions
- no shared static production credential where avoidable
- independent revocation
- short-lived credentials preferred
- auditability

---

# 17. Break-Glass Access

Emergency privileged access SHALL be:

- disabled by default
- individually attributable
- strongly authenticated
- reason-required
- time-limited
- automatically expiring
- immediately alerted
- fully audited
- subject to mandatory post-use review

Permanent undocumented super-admin backdoors are prohibited.

---

# 18. Data Retention and Secure Deletion

Each financial-data class SHALL have:

- documented purpose
- owner
- retention period
- deletion method
- legal/business basis where applicable

Default indefinite retention is prohibited.

Deletion controls SHALL include where applicable:

- secure deletion
- anonymization
- cryptographic erasure
- token revocation
- credential revocation
- backup expiry
- documented deletion verification

Account closure SHALL trigger the approved retention/deletion workflow.

---

# 19. Security Incident Response

The following SHALL be treated as security incidents:

- PAN discovered in BLACKDARK-controlled storage
- CVV/CVC/PIN discovered anywhere
- exposed financial API secret
- unauthorized financial export
- exposed bank credential
- unauthorized privileged financial-data access
- compromised payment webhook secret
- financial-data leakage into logs/analytics/AI
- equivalent high-risk financial-data event

Required workflow:

DETECT  
→ CONTAIN  
→ PRESERVE EVIDENCE  
→ REVOKE / ROTATE  
→ SCOPE  
→ ERADICATE  
→ RECOVER  
→ ESCALATE / NOTIFY WHERE REQUIRED  
→ POST-INCIDENT REVIEW  
→ CONTROL IMPROVEMENT

A written and testable incident playbook SHALL exist.

---

# 20. Supply-Chain Security for Financial Paths

Dependencies touching financial/payment paths SHALL be subject to:

- version pinning/controlled upgrades
- software composition analysis
- vulnerability scanning
- SBOM where supported
- dependency monitoring
- controlled deployment permissions
- review of third-party scripts on payment pages
- minimized third-party JavaScript on sensitive payment flows
- secure release process

---

# 21. Periodic Access Recertification

Sensitive-access permissions SHALL be reviewed periodically.

Review SHALL cover:

- privileged users
- database access
- KMS access
- secret-manager access
- billing administration
- financial integrations
- service identities
- inactive accounts
- emergency-access grants
- excessive/unused permissions

Evidence of review SHALL be retained.

---

# 22. Continuous Security Evidence

Security closure SHALL be based on evidence, not assertions.

Required evidence includes at minimum:

- PAN/CVV scanner results
- secret-scanner results
- MFA coverage proof
- privileged-user inventory
- KMS key inventory
- secret rotation evidence
- resource authorization tests
- Step-Up authentication tests
- webhook signature/replay/idempotency tests
- environment isolation tests
- service identity inventory
- access-review evidence
- audit-integrity evidence
- retention/deletion tests
- incident-response drill/test
- sanitized logging tests
- AI/LLM exclusion tests
- backup/restore and backup-expiry evidence where relevant

---

# 23. Security Acceptance Gate

BLACKDARK Financial Data Security SHALL NOT be marked COMPLETE until all applicable mandatory controls below are PASS with evidence.

| ID | Acceptance Requirement | Requirement |
|---|---|---|
| FDS-01 | PAN does not enter BLACKDARK backend in intended payment flow | MUST |
| FDS-02 | CVV/CVC/PIN/SAD is never stored | MUST |
| FDS-03 | Payment flow is provider-hosted/tokenized | MUST |
| FDS-04 | Bank details use tokenized/provider-hosted flow where available | MUST |
| FDS-05 | Zero PAN/CVV in DB/logs/backups/analytics/CI artifacts | MUST |
| FDS-06 | Financial secrets absent from source and plaintext DB | MUST |
| FDS-07 | Central Secret Manager + KMS/HSM path implemented | MUST |
| FDS-08 | FIPS 140-3 validated path confirmed where applicable | MUST |
| FDS-09 | TLS 1.2+ enforced; TLS 1.3 preferred | MUST |
| FDS-10 | MFA enforced for sensitive privileged access | MUST |
| FDS-11 | Resource-level authorization implemented | MUST |
| FDS-12 | Step-Up implemented for defined high-risk actions | MUST |
| FDS-13 | Service identities are separate/scoped where practical | MUST |
| FDS-14 | Production/staging/development isolation proven | MUST |
| FDS-15 | Sensitive financial data is sanitized from logs | MUST |
| FDS-16 | Security audit trail is tamper-resistant/tamper-evident | MUST |
| FDS-17 | Unusual access and bulk-export alerts exist | MUST |
| FDS-18 | Automated PAN/secret scanning exists | MUST |
| FDS-19 | Webhooks verify signature + replay/idempotency controls | MUST |
| FDS-20 | Retention/deletion policy is implemented and testable | MUST |
| FDS-21 | Financial-data incident playbook exists and is testable | MUST |
| FDS-22 | Break-glass controls exist | MUST |
| FDS-23 | Periodic access recertification exists | MUST |
| FDS-24 | Restricted financial data excluded from AI/LLM pipelines | MUST |
| FDS-25 | Machine-verifiable evidence exists for critical controls | MUST |

---

# 24. Implementation Rules for Cursor / Engineering

1. Inspect the current BLACKDARK architecture before modifying code.
2. Reuse existing secure abstractions where they are already correct.
3. Do not weaken existing security controls.
4. Do not create a new raw-card data path.
5. Do not introduce broad admin bypasses.
6. Do not place secrets in source code or plaintext DB fields.
7. Implement missing controls at the correct architectural layer.
8. Add/update tests for every implemented control.
9. Add migration-safe changes where schema changes are required.
10. Preserve backward compatibility where security does not require breaking behavior.
11. Fail closed for sensitive authorization/security checks.
12. Sanitize all security-sensitive logs.
13. Add machine-verifiable security evidence.
14. Run targeted tests and full regression suite.
15. Do not mark any item PASS without evidence.
16. If a requirement needs external infrastructure, external certification, external provider configuration, or live-production evidence that cannot be produced locally, mark it explicitly:
   - NEEDS_EXTERNAL_VERIFICATION
   - BLOCKED_BY_EXTERNAL_DEPENDENCY
   - NOT LOCALLY PROVABLE
   as appropriate.
17. Never fabricate compliance, certification, production, FIPS, PCI, SOC 2, or live-security evidence.
18. The implementation target is production-grade institutional security, not documentation-only compliance.

---

# 25. Required Final Execution Report

Cursor SHALL return a final report containing:

## A. Executive Status
- COMPLETE / PARTIAL / NOT COMPLETE
- Total controls
- PASS count
- PARTIAL count
- NOT IMPLEMENTED count
- NEEDS_EXTERNAL_VERIFICATION count

## B. Control-by-Control Matrix
For every FDS-01 to FDS-25:
- status
- implementation location
- files changed
- tests
- evidence
- remaining blocker if any

## C. Security Evidence
- exact test commands
- exact test results
- scanner results
- relevant configuration evidence
- migrations
- audit evidence
- authorization tests

## D. Remaining External Dependencies
Explicitly list anything requiring:
- provider dashboard configuration
- production secrets
- production infrastructure
- third-party attestation
- external compliance assessment
- live environment validation

## E. Final Verdict
Cursor MUST state only one:
- FINANCIAL DATA SECURITY: COMPLETE
- FINANCIAL DATA SECURITY: NOT COMPLETE

COMPLETE is allowed only if all applicable mandatory controls have verifiable evidence.

---

# FINAL GOVERNING RULE

BLACKDARK SHALL minimize possession of financial secrets by design. Raw payment authentication data SHALL never enter BLACKDARK-controlled systems where provider-hosted tokenization is available. All remaining financial-sensitive data SHALL be protected through identity-centric Zero Trust, least privilege, strong authentication, centralized cryptographic key management, segmentation, continuous monitoring, controlled retention, incident response, and machine-verifiable security evidence.

**END OF FINAL SPECIFICATION**
