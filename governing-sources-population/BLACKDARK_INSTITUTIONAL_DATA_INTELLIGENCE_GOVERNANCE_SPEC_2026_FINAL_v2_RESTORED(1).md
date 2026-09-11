# BLACKDARK Institutional Data Intelligence, Governance & Operations Specification — v1

**Status:** Governing Source of Truth (SSOT) for the data layer feeding BLACKDARK analytics and the BLACKDARK Decision Truth System  
**Scope:** External/public/provider/user data acquisition, ingestion, normalization, quality, freshness, historical depth, L1/L2/L3, provenance, methodology, reliability, auditability, source licensing, source resilience, API credentials, live-update architecture, and the user-facing “Today’s Decision Surface”.  
**Implementation objective:** Complete all locally-buildable requirements, integrate them into real runtime paths, and leave no known local implementation/integration/test gaps. Production/live and contractual provider evidence remains separately gated and must never be fabricated.

---

# 0. Final Institutional Judgment

BLACKDARK must **not** be designed as “a site that calls APIs”.

It must operate as a governed financial-data system:

```text
SOURCE DISCOVERY / CONTRACT
→ AUTH / LICENSE / ENTITLEMENT
→ INGEST
→ SEQUENCE / GAP CONTROL
→ RAW IMMUTABLE LANDING
→ NORMALIZE
→ QUALITY + FRESHNESS
→ PROVENANCE + LINEAGE
→ HISTORICAL STORE
→ METRIC / FEATURE COMPUTATION
→ DECISION TRUTH SYSTEM
→ USER-FACING DECISION SURFACE
→ AUDIT / REPLAY / OUTCOME
```

The final principle:

> **No critical BLACKDARK decision may be stronger than the weakest material input on which it depends.**

If a required input is stale, missing, unlicensed, ambiguous, low-quality, or methodologically insufficient, the system must **degrade, reject, or abstain** rather than silently fabricate confidence.

---

# 1. Five-Level Mandatory Audit Model

Every material source and every critical derived output must pass five layers.

## Level 1 — Source Authority, Access, Licensing & Legal Use

Verify:
- Who owns/operates the source?
- Official first-party vs aggregator vs community.
- Public vs authenticated.
- API key/account requirements.
- Free vs paid plan.
- Rate limits.
- redistribution/commercial-use terms.
- attribution requirements.
- geographic restrictions.
- contractual SLA availability.
- data retention rights.
- whether derived analytics can be commercially displayed.
- vendor security posture where material.
- personal-data implications where applicable.

**Free access is NOT equivalent to commercial-use permission.**

Required:
```text
SOURCE_ACCESS_CLASSIFIED=true
SOURCE_LICENSE_REVIEW_COMPLETE=true
UNLICENSED_CRITICAL_SOURCE_PATHS=[]
```

---

## Level 2 — Ingestion, Sequencing, Normalization & Reconstruction

Verify:
- WebSocket/stream/bootstrap behavior.
- REST snapshot recovery.
- sequence/update IDs.
- duplicates.
- out-of-order events.
- reconnect.
- missing-message detection.
- snapshot + delta reconstruction.
- idempotency.
- canonical symbols.
- units.
- quote/base orientation.
- timestamps.
- decimal precision.
- venue IDs.
- chain/token identity.
- contract/version identity.

Required:
```text
NORMALIZATION_CONTRACT_PASS=true
SEQUENCE_GAP_CONTROL_PASS=true
RAW_TO_CANONICAL_REPRODUCIBILITY_PASS=true
```

---

## Level 3 — Quality, Freshness, Reliability & Historical Sufficiency

Verify:
- completeness
- timeliness
- accuracy/plausibility
- consistency
- duplication
- source divergence
- stale detection
- coverage
- historical depth
- survivorship/look-ahead bias risks
- source outage behavior

Required:
```text
DATA_QUALITY_GATE_PASS=true
FRESHNESS_POLICY_PASS=true
HISTORICAL_SUFFICIENCY_GATE_PASS=true
SOURCE_RELIABILITY_SCORING_PASS=true
```

---

## Level 4 — Provenance, Methodology, Auditability & Governance

Every material derived number must answer:

```text
Where did this come from?
Which raw observations were used?
When were they observed?
What transformations were applied?
Which methodology version produced the result?
Can the result be reproduced later?
```

Required:
```text
PROVENANCE_PASS=true
DATA_LINEAGE_TRACEABILITY_PASS=true
METHODOLOGY_VERSIONING_PASS=true
AUDIT_REPLAY_PASS=true
```

---

## Level 5 — Decision Safety, User Truth & Differentiation

Data only becomes a user-facing decision input after:
- freshness gate
- quality gate
- evidence sufficiency
- execution feasibility where relevant
- risk gate
- uncertainty disclosure
- Decision Truth admission gate

Required:
```text
NO_UNGATED_CRITICAL_DATA_TO_DECISION_PATHS=[]
ABSTAIN_ON_INSUFFICIENT_INPUTS=true
```

---

# 2. Standards and Institutional Reference Position

The implementation must use the following as governing/best-practice references according to applicability:

1. **NIST AI RMF 1.0** — trustworthy/responsible AI risk management; use for data/model governance, transparency, reliability and lifecycle controls.
2. **ISO/IEC 42001:2023** — AI management-system governance; use as institutional management-system reference.
3. **BCBS 239** — use as a **best-practice benchmark** for accuracy, integrity, completeness, timeliness, adaptability, aggregation and traceability of risk data. Do not falsely claim BLACKDARK is a regulated bank or formally subject to BCBS 239 unless legally true.
4. **EU AI Act Article 10** — apply only when the relevant AI system/use is within the Article’s legal scope; do not label all BLACKDARK data as legally subject to Article 10 by default.
5. **GDPR / applicable privacy law** — apply to personal data according to jurisdiction and role. Separate personal/user data from public market data governance.
6. **GLBA / FTC Safeguards Rule** — legal applicability must be determined; do not assume applicability merely because BLACKDARK is financial analytics. If applicable, implement required safeguards and service-provider oversight.
7. Provider official API documentation and terms are authoritative for access, authentication, update cadence, limits and allowed use.

Required:
```text
LEGAL_APPLICABILITY_REGISTER_EXISTS=true
NO_FALSE_REGULATORY_SCOPE_CLAIMS=[]
```

---

# 3. Correction of Recommendation #1

The supplied recommendation contains a strong institutional core, but the following correction is mandatory.

### Keep
- lineage for every critical decision
- provenance + freshness on critical outputs
- normalization
- historical-depth sufficiency
- fallback/degrade/abstain
- methodology cards
- separation of user data and public market data
- provider security review
- internal SLO
- GLBA applicability determination
- BCBS 239 as a best-practice data-governance benchmark
- Today’s Decision Surface

### Correct
The rule:

> “Primary paid/reliable is required for critical paths.”

is too absolute.

**Final rule:**

> A critical path needs an approved, legally usable, reliability-qualified source strategy with redundancy and measurable SLOs. A paid source is not automatically required if an official first-party public feed provides the required data and usage rights. A paid/contractual source becomes mandatory only when the required reliability, licensing, historical depth, SLA, coverage or data type cannot be defensibly achieved otherwise.

### Reject
- “paid = reliable” as an automatic equivalence.
- “free = unsafe” as an automatic equivalence.
- one-source dependency for critical decisions.
- using free/community data commercially without terms review.
- claiming enterprise SLA when only public/free APIs are used.

---

# 4. Complete Source Taxonomy BLACKDARK Needs

## DAT-001 — Centralized Exchange Spot Market Data

Required fields:
- instruments
- best bid/ask
- trades
- ticker
- OHLCV
- L2 order book
- venue status
- deposit/withdrawal status where available
- fees where programmatically/contractually available

Preferred strategy:
- direct official venue WebSocket for live market data
- REST for bootstrap/backfill/recovery
- aggregator only as secondary/coverage augmentation

Candidate direct venues include:
- Binance
- Coinbase
- Kraken
- OKX
- Bybit
- other supported venues after source qualification

---

## DAT-002 — Derivatives Data

Required where applicable:
- perpetual/futures prices
- mark/index price
- funding
- open interest
- liquidation data
- basis
- term structure
- options IV/skew/Greeks if supported
- contract metadata

Use direct venue feeds first where practicable.

---

## DAT-003 — Order-Book Microstructure

Required for execution-sensitive Decision Truth features:
- L1 best bid/ask
- L2 aggregated depth
- update sequence
- local book reconstruction
- depth imbalance
- spread
- impact curves
- fill/capacity estimates

L3:
- individual order-level events where the venue exposes them and methodology needs them.

**L3 is NOT globally mandatory.**
It is mandatory only for a feature whose methodology genuinely requires order-level queue/order identity and where lawful/available.

---

## DAT-004 — On-Chain Raw Data

Sources:
- own blockchain node where feasible
- official JSON-RPC compatible nodes
- qualified RPC provider(s) as operational fallback
- chain indexers only as secondary/derived sources unless specifically approved

Data:
- blocks
- transactions
- logs/events
- token transfers
- contract state
- gas/base fees
- validators/staking where applicable
- bridge/oracle events

Ethereum-compatible chains should preserve:
- block number/hash
- tx hash
- log index
- contract address
- chain ID
- confirmation/finality state

---

## DAT-005 — DeFi Protocol Data

Data categories:
- TVL
- DEX volumes
- fees/revenue
- pools
- yields
- borrow rates
- utilization
- liquidity
- bridges
- stablecoin supply/distribution
- token unlocks
- protocol treasuries
- open interest/funding where applicable
- protocol security/hack history

Preferred hierarchy:
1. raw/on-chain protocol contracts
2. official protocol APIs/subgraphs
3. qualified aggregators such as DefiLlama/Dune for enrichment and acceleration

Never treat aggregator labels/calculations as raw chain truth without provenance.

---

## DAT-006 — Stablecoin Data

Required:
- spot price across multiple venues
- depth/liquidity
- supply
- chain distribution
- mint/burn if available
- redemption/issuer data where public
- reserve/attestation references where available
- depeg duration and magnitude
- cross-venue divergence

---

## DAT-007 — Oracle Data

Required:
- oracle price
- timestamp
- update heartbeat where available
- deviation behavior
- source/feed identity
- chain/feed address
- stale state
- divergence vs market composite

Examples may include Chainlink and protocol-native oracle feeds.

---

## DAT-008 — Wallet / Entity / Smart-Money Data

Data:
- wallet transactions
- balances
- flow
- counterparties
- cluster relationships
- labels
- historical behavior

Rules:
- raw on-chain facts are separate from entity attribution.
- labels must retain source + confidence.
- paid labels are not mandatory unless free/public methodology cannot support the required feature.
- no unsupported identity claims.

---

## DAT-009 — Macro / Rates / Liquidity

Sources can include:
- FRED/ALFRED
- central banks
- official statistical agencies
- treasury/sovereign data sources

Data:
- rates
- inflation
- employment
- money/liquidity
- yield curves
- USD/liquidity proxies
- release calendars

Macro data is release/event driven, not millisecond market data.

---

## DAT-010 — Regulatory / Public Filings

Sources:
- SEC EDGAR/data.sec.gov
- other official regulator feeds as geographically relevant

Data:
- filings
- material disclosures
- ETF/fund disclosures where available
- company crypto holdings disclosures
- issuer updates

Prefer original regulatory sources over news summaries.

---

## DAT-011 — News / Events

Source hierarchy:
1. official issuer/protocol/exchange/regulator announcements
2. high-quality licensed news providers
3. qualified secondary news feeds
4. social/community only as weak evidence unless independently confirmed

Every news-derived decision input requires:
- publication time
- observed time
- source identity
- confidence
- corroboration status

---

## DAT-012 — Social / Sentiment

Use only as supporting evidence.

Required:
- platform/source
- sampling methodology
- bot/sybil controls
- language coverage
- timestamp
- volume
- confidence
- manipulation risk

Social sentiment must never override materially stronger market/on-chain evidence automatically.

---

## DAT-013 — Security / Incident / Venue Health

Sources:
- exchange status pages/APIs
- blockchain status
- protocol incident announcements
- exploit/security feeds
- internal source-health telemetry

Used for:
- Exchange Health
- provider reliability
- Decision Truth Safety Floor
- Pre-Impact Protection

---

## DAT-014 — User/Portfolio Data

Only when user deliberately connects/provides it.

Possible sources:
- read-only exchange API
- read-only wallet addresses
- user-entered portfolio
- institutional integrations

Rules:
- separate governance domain
- least privilege
- read-only by default for analytics
- encryption
- explicit authorization
- purpose limitation
- revocation
- no silent sharing with market-data providers

---

# 5. Provider Access / Keys / Account Activation Matrix

## Public market data — no account/key where supported

Examples from current official documentation:
- Coinbase Advanced Trade public market-data channels: most public channels need no authentication.
- Bybit public WebSocket streams: public endpoints available without private account authentication.
- OKX: public WebSocket service for public subscriptions.
- Binance: public market streams are WebSocket feeds; authenticated/private data is separate.

BLACKDARK must use unauthenticated public feeds where they legally and technically satisfy the requirement.

## Free account/API key

Examples:
- FRED API requires an API key tied to a FRED account.
- some aggregator/RPC services may require free API keys even for no-cost tiers.

## Authenticated user/private data

Examples:
- exchange private/user channels require credentials/JWT/API keys.
- use only when a user explicitly connects an account and within the project’s safety/permissions policy.

## Paid/contractual

Needed when:
- commercial license requires it
- required historical depth is unavailable free
- contractual SLA is required
- rate limits are insufficient
- enterprise redistribution rights are required
- institutional labels/derived data cannot be lawfully produced otherwise

Required:
```text
SOURCE_CREDENTIAL_REQUIREMENTS_REGISTRY_PASS=true
TEST_LIVE_CREDENTIAL_SEPARATION_PASS=true
SECRET_MANAGER_ONLY_PASS=true
HARDCODED_PROVIDER_SECRETS=[]
```

---

# 6. Secrets and Credential Governance

All keys/tokens/secrets:
- secrets manager/environment secret store only
- never source control
- never logs
- least privilege
- separate test/live
- rotation capability
- revoke capability
- owner + purpose
- expiry where supported
- quota visibility

Public-data APIs that need no key must not be forced behind unnecessary secret management.

---

# 7. Is Reliance on Free Sources Dangerous?

## Final answer

**Free is not inherently dangerous. Single-source, unlicensed, unmonitored and SLA-less dependency is dangerous.**

Risk dimensions:
- no contractual uptime
- lower quotas
- historical-depth limits
- sudden policy/pricing change
- restricted commercial redistribution
- no support
- schema changes
- IP/geographic blocking
- incomplete coverage
- delayed data
- missing advanced fields/L2/L3
- insufficient backfill

Free sources may be fully acceptable for:
- official public exchange WebSockets
- official regulator data
- official chain RPC if self-hosted
- development
- non-critical enrichment
- redundancy

Free-only is **not** acceptable as a design doctrine for every critical path.

Required:
```text
FREE_SOURCE_RISK_REGISTER_PASS=true
SINGLE_SOURCE_CRITICAL_DEPENDENCIES=[]
```

---

# 8. Will Not Paying Stop BLACKDARK?

## Final answer

**No — the architecture must not make payment to one vendor a prerequisite for the entire site.**

Without paid vendors, BLACKDARK can still operate a substantial core using:
- official public exchange streams
- official public blockchain data / RPC
- regulator/public macro data
- allowed free APIs
- internally accumulated history

But the following may be limited until paid/contractual data or sufficient self-collected history exists:
- deep historical L2/L3
- high-rate historical tick archives
- premium entity/wallet labels
- certain options/derivatives history
- enterprise SLA
- redistribution rights for some datasets
- rapid bulk backfill
- specialized institutional datasets

Correct behavior:
```text
CAPABILITY_AVAILABLE
CAPABILITY_DEGRADED
CAPABILITY_ABSTAINED
CAPABILITY_UNAVAILABLE
```

Never fake completeness.

---

# 9. Real-Time Update Architecture

## DAT-015 — WebSocket-first for live market data

For suitable venues:
- persistent WebSocket
- heartbeat
- reconnect
- snapshot bootstrap
- delta application
- sequence validation
- replay queue during snapshot
- gap detection
- forced resnapshot on gap
- source timestamps
- observed timestamps
- ingest timestamps

---

## DAT-016 — REST for bootstrap/backfill/recovery

REST is not the primary mechanism for high-frequency book updates when a reliable stream exists.

Use REST for:
- instrument metadata
- initial snapshots
- recovery
- periodic reconciliation
- historical candles/trades
- source-health validation

---

## DAT-017 — Chain/event-driven update

On-chain data updates:
- by new block
- by logs/event subscriptions where supported
- finality-aware
- reorg-aware

Do not label an unfinalized state as final.

---

## DAT-018 — Release/event-driven non-market data

Macro/regulatory/news data should refresh on:
- official release
- filing
- announcement
- event

Polling faster than source publication cadence adds no truth.

---

# 10. Freshness Classes and Update Targets

Exact SLOs must be empirically calibrated per source and product. Do not promise a universal update speed.

Initial engineering classes:

| Class | Data | Ingest method | Target behavior |
|---|---|---|---|
| T0 | L1/L2 trades/order book | WebSocket | process source events immediately; detect stale within seconds |
| T1 | ticker/price/funding/OI/liquidations | WS/fast API | seconds |
| T2 | on-chain block/events | block/event driven | source-chain cadence |
| T3 | DeFi/protocol aggregates | event/API | seconds to minutes depending source |
| T4 | news/status/incidents | event/poll | near event time |
| T5 | macro/regulatory | release driven | immediately after official release |
| T6 | slow fundamentals | scheduled | minutes/hours/daily as justified |

Every critical output must expose:
```text
source_timestamp
observed_at
ingested_at
last_successful_update
age_seconds
freshness_state
```

Freshness states reuse canonical Failure/Decision Truth semantics:
```text
LIVE
NEAR_LIVE
DELAYED
STALE
CACHED
PARTIAL
UNKNOWN
```

---

# 11. L1 / L2 / L3 Final Policy

## L1
Best bid/ask/top-of-book.
Useful for:
- spread
- lightweight price monitoring

Not sufficient for:
- robust slippage
- meaningful capacity
- market impact

## L2
Aggregated depth by price level.

**Mandatory for execution-sensitive features whenever the venue exposes it**, including:
- expected slippage
- liquidity
- depth imbalance
- capacity
- realizable Net Edge
- Execution Feasibility

## L3
Individual order-level/order-ID detail.

Use only:
- where venue provides it
- where licensing permits
- where methodology proves incremental value

Coinbase official Exchange documentation exposes full/Level3 mechanisms; therefore L3 is technically available on at least some venues, but it must not be assumed universal.

Required:
```text
L2_REQUIREMENT_BY_FEATURE_PASS=true
L3_REQUIREMENT_BY_FEATURE_PASS=true
FALSE_L3_UNIVERSAL_REQUIREMENTS=[]
```

---

# 12. Historical Depth Policy

Historical data must be assessed **per calculation**, not by one arbitrary global duration.

Each methodology declares:
```text
minimum_history
preferred_history
sampling_frequency
required_market_regimes
required_venue_coverage
missing_data_tolerance
```

## Storage tiers

1. **Raw hot stream** — recent high-resolution events/order book.
2. **Raw warm archive** — compressed event history.
3. **Canonical normalized history** — queryable normalized data.
4. **Derived feature history** — versioned calculated metrics.
5. **Audit/replay store** — enough raw/canonical evidence to reproduce critical decisions.

Start capturing L2/tick history immediately, because free historical order-book depth is often the hardest dataset to reconstruct later.

A Grade/Simulation must not be issued if historical sufficiency fails.

---

# 13. Canonical Normalization Contract

Every record must map into canonical identities.

At minimum:
```text
source_id
venue_id
market_type
instrument_id
base_asset
quote_asset
canonical_asset_ids
chain_id
contract_address_if_applicable

event_type
source_timestamp
observed_at
ingested_at
sequence_id_if_available

price
quantity
side
currency
unit
precision

raw_payload_reference
schema_version
normalization_version
```

Rules:
- Decimal for financial values at critical boundaries.
- never silently coerce unknown currencies/assets.
- canonical symbol mapping is versioned.
- token identity must use chain + contract, not ticker alone.
- timestamp semantics are UTC-aware internally.
- original raw event remains traceable.

---

# 14. Raw Immutable Landing Zone

Before destructive normalization:
store or retain reproducible access to raw source evidence for material feeds according to retention/licensing constraints.

Required:
- raw payload hash
- source
- receive time
- source time
- schema version
- partition
- retention class

Do not overwrite raw evidence with normalized data.

---

# 15. Provenance / Lineage Contract

Every critical metric/decision must expose machine-readable lineage.

Minimum lineage graph:
```text
decision_id
→ metric_ids
→ transformation_ids
→ normalized_record_ids
→ raw/source references
```

Each node includes:
- timestamp
- version
- source
- hash/reference
- quality state

Required:
```text
CRITICAL_DECISION_LINEAGE_COVERAGE=100%
UNTRACEABLE_CRITICAL_METRICS=[]
```

---

# 16. Methodology Cards

Every derived metric must have a methodology card containing:

- name
- purpose
- formula
- inputs
- source requirements
- freshness limits
- historical-depth requirement
- normalization assumptions
- exclusions
- confidence/uncertainty
- failure behavior
- methodology version
- validation tests
- owner

Applies at minimum to:
- Net Edge
- Realizable Net Edge
- Execution Feasibility
- Capacity
- Risk
- Evidence Grade
- Stablecoin Health
- Exchange Health
- Smart Money score
- Whale/cluster confidence
- Simulation
- Calibration
- Decision Admission

---

# 17. Quality Gate

Each material dataset gets:

```text
completeness_score
timeliness_score
consistency_score
plausibility_score
cross_source_agreement
provenance_status
historical_sufficiency
quality_state
```

Canonical quality states:
```text
COMPLETE
PARTIAL
CONFLICTING
INSUFFICIENT
SUSPECT
UNVERIFIED
```

Critical decisions cannot treat all states as equal.

---

# 18. Cross-Source Reconciliation

For high-value market facts:
- compare direct venue vs secondary provider where available
- detect large divergence
- record source disagreement
- do not average blindly
- identify authoritative source for venue-specific facts
- use robust composite methodology only where documented

Required:
```text
CROSS_SOURCE_DIVERGENCE_DETECTION_PASS=true
SILENT_SOURCE_CONFLICT_PATHS=[]
```

---

# 19. Reliability Engineering

Every provider/source receives operational telemetry:

- availability
- reconnect count
- latency
- event lag
- stale incidents
- schema errors
- sequence gaps
- rate-limit events
- HTTP errors
- coverage
- recovery time

Derive:
```text
SOURCE_RELIABILITY_SCORE
```

Do not confuse this operational score with legal/contractual SLA.

---

# 20. SLA vs SLO

## External SLA
Only claim if contractual/provider terms actually provide it.

## Internal SLO
BLACKDARK must define source-class SLOs even when the provider offers no SLA.

At minimum:
- availability target
- freshness target
- recovery target
- max acceptable gap
- fallback trigger
- abstain trigger

Required:
```text
SOURCE_SLO_REGISTRY_PASS=true
FALSE_EXTERNAL_SLA_CLAIMS=[]
```

---

# 21. Source Redundancy and Failover

For every critical Decision Truth dependency classify:

```text
PRIMARY
SECONDARY
DERIVED_FALLBACK
NO_SAFE_FALLBACK
```

If no safe fallback:
failure must trigger abstention/unavailable rather than synthetic data.

Required:
```text
FALLBACK_OR_DEGRADE_PATH_DEFINED=true
CRITICAL_SINGLE_POINT_SOURCE_FAILURES=[]
```

---

# 22. Rate-Limit / Quota Management

Track:
- per provider
- per endpoint
- minute/hour/day/month
- remaining quota where available
- cost per call where applicable
- retry-after
- backoff
- priority class

Critical data requests get priority over noncritical UI refresh.

Never solve a quota limit by violating provider terms or uncontrolled key rotation.

---

# 23. Licensing / Redistribution Gate

Before public production display, each external source must have a recorded use decision:

```text
INTERNAL_ANALYSIS_ALLOWED
DERIVED_OUTPUT_ALLOWED
PUBLIC_DISPLAY_ALLOWED
REDISTRIBUTION_ALLOWED
ATTRIBUTION_REQUIRED
COMMERCIAL_USE_ALLOWED
```

Unknown = not approved for production display until reviewed.

This is particularly important for aggregator datasets whose public/free access may have commercial-use restrictions.

---

# 24. User Data Separation

Public market/on-chain source stores must be logically separated from:
- account profile
- connected exchange credentials
- portfolio data
- alerts/preferences
- personal analytics

Required:
- least privilege
- access control
- purpose limitation
- retention policy
- encryption
- deletion/export workflows as legally applicable

---

# 25. GLBA Applicability

Create a documented legal determination:

```text
GLBA_APPLICABILITY_STATUS =
APPLICABLE
NOT_APPLICABLE
LEGAL_REVIEW_REQUIRED
```

Do not force `true/false` before legal review.

If applicable:
- Safeguards program
- customer information protection
- service-provider oversight
- incident requirements as applicable

---

# 26. Data Retention

Define per data class:
- raw market
- normalized market
- L2/L3
- on-chain
- news
- user personal
- audit evidence
- decision/outcome ledger

Retention must consider:
- methodology reproducibility
- licensing
- privacy
- storage cost
- legal obligations

---

# 27. Schema Evolution

Providers change schemas.

Required:
- schema version
- parser version
- contract tests
- unknown-field tolerance where safe
- breaking-change alarms
- replay fixtures
- backward-compatible canonical layer

---

# 28. Clock / Timestamp Integrity

Reuse BLACKDARK Global Time SSOT.

Store:
- source timestamp
- exchange/matching-engine timestamp if available
- observed time
- ingest time

Never replace source time with local arrival time.

Use latency fields:
```text
source_to_observed_ms
observed_to_ingested_ms
```

---

# 29. Reorg / Finality Integrity for On-Chain Data

On-chain inputs must track:
```text
PROPOSED
SAFE
FINALIZED
REORGED
```
or chain-appropriate equivalent.

Any decision sensitive to finality must use the correct state.

---

# 30. Historical Bias Controls

Backtests/grades must guard against:
- survivorship bias
- look-ahead bias
- delisted asset omission
- future symbol mappings
- post-event labels
- revised macro data without vintage control
- cherry-picking

Use ALFRED/vintage-aware data where historical macro revisions matter.

---

# 31. Today's Decision Surface — Final Differentiating Product

This should be implemented.

It must **not** be another price dashboard.

At any time of day, the default surface answers:

## A. What is my state?
- portfolio/risk state if available
- major exposures
- Risk Budget use

## B. What materially changed since my last meaningful state?
Only top 3–5 changes, evidence-backed.

## C. What opportunities survived the truth gates?
Show only admitted opportunities after:
- quality
- freshness
- Net Edge
- execution feasibility
- risk
- evidence
- uncertainty

## D. What did BLACKDARK reject?
Show rejected attractive-looking opportunities and **Why NOT**.

## E. What can hurt me next?
- venue deterioration
- depeg
- liquidity collapse
- concentration
- funding/liquidation stress
- source degradation where material

## F. What does BLACKDARK not know?
Explicit:
```text
NO DECISION
INSUFFICIENT EVIDENCE
SOURCE CONFLICT
STALE INPUT
```

## G. Evidence strip
Every critical card includes:
- source class
- as_of
- freshness
- quality
- confidence/evidence
- methodology version
- “View evidence”

---

# 32. Why This Can Be a Real Differentiator

The moat is not the data feed itself; large competitors can buy the same data.

The differentiation is the governed chain:

```text
raw market/on-chain facts
→ validated / normalized evidence
→ source reliability
→ economic truth
→ execution feasibility
→ portfolio impact
→ admission / rejection / abstention
→ auditable explanation
```

The user sees not:
> “BTC moved 3%”

but:
> “Three material things changed. Two attractive-looking opportunities were rejected because the edge disappears after execution. One remains viable within your risk budget. Evidence is current and the decision expires in X.”

The result is a **Decision Truth Surface**, not a data terminal.

---

# 33. Continuous Update / Push Architecture

Backend:
- source adapters
- streaming bus/event layer
- normalization workers
- quality/freshness service
- canonical stores
- derived metric workers
- Decision Truth evaluation
- alert/event router

Frontend:
- WebSocket/SSE from BLACKDARK backend
- not direct browser connections to dozens of vendors
- incremental card updates
- freshness countdown/state
- material-change updates
- deduplication

Only recompute affected metrics when inputs materially change where feasible.

---

# 34. Material Change Engine

Do not refresh every card merely because one second passed.

Define:
```text
MATERIAL_CHANGE
NON_MATERIAL_UPDATE
STALE_TRANSITION
QUALITY_CHANGE
DECISION_CHANGE
```

This reduces noise and creates a superior user experience.

---

# 35. Decision Expiry

Every time-sensitive decision gets:
```text
evaluated_at
valid_until_or_review_at
expiry_reason
```

If critical market inputs exceed freshness limits:
decision is no longer shown as current.

---

# 36. Data Confidence Is Multi-Dimensional

Do not collapse everything into one “confidence %”.

Expose internally:
- source reliability
- data quality
- freshness
- cross-source agreement
- historical sufficiency
- methodology confidence
- decision calibration

A user-facing summary can aggregate only with documented methodology and drill-down.

---

# 37. Free-First Launch Strategy

BLACKDARK may launch engineering with a **free-first but not free-dependent** architecture.

### Phase A — No/low paid dependency
- official exchange public market streams
- public chain/RPC/self-host where feasible
- FRED
- SEC
- approved free DeFi endpoints
- internal history accumulation
- own derived analytics

### Phase B — Buy only proven bottlenecks
Pay only where measured evidence shows:
- quota is blocking
- history is insufficient
- licensing requires commercial plan
- SLA is needed
- institutional data quality materially improves
- user value/revenue justifies it

Required:
```text
PAID_DATA_PURCHASES_REQUIRE_VALUE_CASE=true
```

---

# 38. Data Vendor Exit Strategy

No critical proprietary vendor schema may leak throughout product code.

Use adapters into canonical contracts.

Changing vendor should not require rewriting Decision Truth.

Required:
```text
VENDOR_LOCK_IN_AT_CANONICAL_BOUNDARY=false
```

---

# 39. Minimum Production-Critical Source Redundancy

For each critical class define redundancy by semantics.

Example:
- venue-specific order book: authoritative direct venue feed + recovery path; secondary aggregator cannot replace venue truth if semantics differ.
- composite/reference price: multiple qualified venues.
- stablecoin health: multi-venue + on-chain/issuer context.
- macro: original official source preferred; mirror/cache for availability.
- news: authoritative original source where event-specific.

Do not mechanically require “two vendors” if one is the authoritative primary; require a defensible failure strategy.

---

# 40. Monitoring Dashboard for Data Operations

Internal dashboard must show:
- source status
- connections
- lag
- stale feeds
- sequence gaps
- quality failures
- last success
- quota
- error rate
- historical gaps
- failed normalization
- fallback state
- affected capabilities
- affected decisions/users

---

# 41. Source Health Must Affect Product Truth

If a source degrades, user-facing decision state changes.

No green operational dashboard while user decision still pretends data is live.

Required:
```text
SOURCE_HEALTH_TO_DECISION_SAFETY_WIRING_PASS=true
```

---

# 42. Auditability

For any critical historic decision, an authorized auditor must be able to reconstruct:

1. what user saw
2. what source data existed
3. which versions were used
4. which transformations ran
5. data quality/freshness state
6. decision output
7. why it passed/rejected/abstained

Required:
```text
CRITICAL_DECISION_REPLAY_PASS=true
```

---

# 43. Reliability / Chaos Tests

Test:
- stream disconnect
- message gap
- duplicate message
- out-of-order message
- stale feed
- corrupt payload
- schema change
- 429
- 5xx
- DNS/provider outage
- one venue divergence
- on-chain reorg
- RPC lag
- aggregator failure
- quota exhaustion
- secret missing/expired

Verify:
- no silent corruption
- correct degradation
- recovery/replay
- user truth state

---

# 44. Source Registry — Mandatory Schema

Create one canonical registry containing:

```text
source_id
provider
dataset
source_type
officiality
endpoint_class
auth_type
credential_name
test/live
commercial_use_status
redistribution_status
attribution_requirement
rate_limit
contractual_sla
internal_slo
expected_cadence
freshness_threshold
historical_depth
L1/L2/L3
primary/secondary
fallback
data_owner
security_review
legal_review
schema_version
parser_version
status
```

---

# 45. Required Source Classes for Full BLACKDARK Capability

Before final engineering closure, the repository must have implemented/adaptable source contracts for all applicable classes:

```text
CEX_SPOT
CEX_DERIVATIVES
ORDER_BOOK
ONCHAIN_RPC
DEFI
STABLECOIN
ORACLE
WALLET_ENTITY
MACRO
REGULATORY
NEWS_EVENT
SOCIAL_SENTIMENT
SECURITY_INCIDENT
USER_PORTFOLIO
```

Not every class requires a paid vendor or live key during local engineering, but every locally-buildable adapter/contract/fallback/quality behavior must be complete.

---

# 46. Source Qualification Score

Each source can be internally scored across:
- authority
- licensing clarity
- uptime
- latency
- coverage
- historical depth
- schema stability
- data quality
- support
- cost
- portability

The score is advisory; do not let a high composite score override a hard legal/licensing failure.

---

# 47. Minimum “No Payment” Viable Data Stack

The system should be able to run a non-fabricated core using:

- official public CEX WebSockets/REST where permitted
- official public blockchain data / self-hosted or approved RPC access
- official public regulator feeds
- FRED API with free account key
- approved free DeFi endpoints
- internal normalization/quality/history/Decision Truth

If a source is not available:
capability degrades or abstains; platform does not lie.

---

# 48. What Paid Data Can Add Later

Paid data is justified for:
- contractual SLA
- redistribution rights
- premium historical L2/L3/tick depth
- premium wallet/entity labels
- enterprise bulk data
- high throughput
- lower latency/direct feeds
- premium support
- specialized options/derivatives datasets
- institutional legal/commercial license

Purchasing is a business optimization, not an architectural rescue.

---

# 49. User-Facing Provenance Standard

On critical cards show concise provenance:

```text
Sources: 4 direct venues + on-chain confirmation
As of: 12:48:03 local time
Freshness: LIVE
Quality: COMPLETE
Evidence: A / SHADOW_LIVE
Methodology: NetEdge v3.2
```

“View evidence” exposes full trace.

Do not overwhelm basic users with raw technical metadata by default.

---

# 50. Data Use / Decision Disclosure

User-facing language:
- distinguish observation vs inference
- distinguish historical vs live
- distinguish simulated vs realized
- disclose delayed/cached data
- explain uncertainty
- do not guarantee outcome

---

# 51. Mandatory Implementation Gates

The implementation may claim `PASS_ENGINEERING_DATA_INTELLIGENCE=true` only if all locally-buildable gates pass:

```text
SOURCE_SPEC_FULL_READ=true
SOURCE_REQUIREMENTS_ACCOUNTED_FOR=100%

SOURCE_REGISTRY_PASS=true
SOURCE_ACCESS_CLASSIFIED=true
SOURCE_LICENSE_REVIEW_ARCHITECTURE_PASS=true
SOURCE_CREDENTIAL_REQUIREMENTS_REGISTRY_PASS=true
SECRET_MANAGER_ONLY_PASS=true
TEST_LIVE_CREDENTIAL_SEPARATION_PASS=true

INGESTION_ADAPTER_CONTRACT_PASS=true
WEBSOCKET_RECONNECT_PASS=true
SNAPSHOT_DELTA_RECONSTRUCTION_PASS=true
SEQUENCE_GAP_CONTROL_PASS=true
IDEMPOTENT_INGEST_PASS=true

NORMALIZATION_CONTRACT_PASS=true
CANONICAL_ASSET_IDENTITY_PASS=true
CANONICAL_INSTRUMENT_IDENTITY_PASS=true
FINANCIAL_DECIMAL_BOUNDARY_PASS=true
UTC_TIMESTAMP_INTEGRITY_PASS=true

RAW_IMMUTABLE_EVIDENCE_PASS=true
PROVENANCE_PASS=true
DATA_LINEAGE_TRACEABILITY_PASS=true
METHODOLOGY_VERSIONING_PASS=true

DATA_QUALITY_GATE_PASS=true
FRESHNESS_POLICY_PASS=true
SOURCE_RELIABILITY_SCORING_PASS=true
CROSS_SOURCE_DIVERGENCE_DETECTION_PASS=true

HISTORICAL_DEPTH_POLICY_PASS=true
HISTORICAL_SUFFICIENCY_GATE_PASS=true
L2_REQUIREMENT_BY_FEATURE_PASS=true
L3_REQUIREMENT_BY_FEATURE_PASS=true

SOURCE_SLO_REGISTRY_PASS=true
FALLBACK_OR_DEGRADE_PATH_DEFINED=true
ABSTAIN_ON_INSUFFICIENT_INPUTS=true
SOURCE_HEALTH_TO_DECISION_SAFETY_WIRING_PASS=true

RATE_LIMIT_QUOTA_GOVERNANCE_PASS=true
SCHEMA_EVOLUTION_PASS=true
ONCHAIN_FINALITY_REORG_PASS=true

USER_DATA_SEPARATION_PASS=true
RETENTION_POLICY_PASS=true
LEGAL_APPLICABILITY_REGISTER_EXISTS=true

TODAYS_DECISION_SURFACE_PASS=true
MATERIAL_CHANGE_ENGINE_PASS=true
DECISION_EXPIRY_PASS=true
USER_FACING_PROVENANCE_PASS=true

CRITICAL_DECISION_REPLAY_PASS=true
DATA_FAILURE_INJECTION_MATRIX_PASS=true

KNOWN_LOCAL_DATA_GAPS=[]
KNOWN_LOCAL_DATA_DEFECTS=[]
KNOWN_LOCAL_DATA_INTEGRATION_GAPS=[]
KNOWN_LOCAL_DATA_TEST_GAPS=[]

LOCAL_BUILDABLE_DATA_REQUIREMENTS_REMAINING=0
PARTIALLY_IMPLEMENTED_LOCAL_DATA_REQUIREMENTS=0
UNIMPLEMENTED_LOCAL_DATA_REQUIREMENTS=0
UNVERIFIED_LOCAL_DATA_REQUIREMENTS=0

PASS_ENGINEERING_DATA_INTELLIGENCE=true
READY_FOR_INTENDED_LOCAL_USE=true
PASS_LIVE_NOT_CLAIMED=true
```

---

# 52. Anti-Bypass Gates

Required empty:

```text
RAW_TO_DECISION_BYPASS_PATHS=[]
UNNORMALIZED_CRITICAL_DATA_PATHS=[]
NO_PROVENANCE_CRITICAL_OUTPUTS=[]
NO_FRESHNESS_CRITICAL_OUTPUTS=[]
QUALITY_GATE_BYPASS_PATHS=[]
SOURCE_HEALTH_BYPASS_PATHS=[]
UNLICENSED_PRODUCTION_DATA_PATHS=[]
UNVERSIONED_CRITICAL_METHODOLOGIES=[]
UNAUDITABLE_CRITICAL_DECISIONS=[]
STALE_AS_LIVE_PATHS=[]
PARTIAL_AS_COMPLETE_PATHS=[]
UNKNOWN_AS_TRUSTED_PATHS=[]
```

---

# 53. No-Deferral Rule

The following are **not** acceptable LIVE-gate excuses:
- missing adapter code
- missing normalization
- missing quality rules
- missing fallback logic
- missing provenance
- missing local history capture
- missing storage schema
- missing tests
- missing credentials registry
- missing rate-limit handling
- missing source-health monitoring
- missing Decision Truth wiring

These must be built locally.

Valid live/external gates include only things that require:
- actual provider credentials
- actual contractual/license confirmation
- actual production traffic
- actual live latency/SLA observation
- external legal opinion
- paid dataset purchase
- historical data that cannot be reconstructed locally

---

# 54. Final Live Verification Register

Do not claim `PASS_LIVE` until actual evidence exists for applicable items:

```text
LIVE_SOURCE_CONNECTIVITY_VERIFIED
LIVE_SOURCE_AUTH_VERIFIED
LIVE_RATE_LIMIT_BEHAVIOR_VERIFIED
LIVE_WEBSOCKET_RECONNECT_VERIFIED
LIVE_SEQUENCE_GAP_RECOVERY_VERIFIED
LIVE_MARKET_DATA_LATENCY_VERIFIED
LIVE_L2_DEPTH_VERIFIED
LIVE_L3_IF_REQUIRED_VERIFIED
LIVE_ONCHAIN_FINALITY_VERIFIED
LIVE_SOURCE_FAILOVER_VERIFIED
LIVE_SOURCE_RELIABILITY_SLO_VERIFIED
LIVE_HISTORICAL_BACKFILL_VERIFIED
LIVE_USER_FACING_FRESHNESS_VERIFIED
LIVE_DECISION_DEGRADE_ABSTAIN_VERIFIED
LIVE_PROVENANCE_TRACE_VERIFIED
LIVE_PROVIDER_LICENSE_ENTITLEMENT_VERIFIED
```

---

# 55. Final Implementation Priority

## P0 — mandatory now
- source registry
- access/license/credentials registry
- direct CEX public market adapters
- streaming + snapshot/delta/gap control
- canonical normalization
- raw evidence
- provenance/lineage
- quality/freshness
- L2 for execution-sensitive paths
- own history capture
- source health/reliability
- fallback/degrade/abstain
- Decision Truth wiring
- Today’s Decision Surface
- audit replay
- quota/schema/security controls

## P1 — high value
- broader CEX/DEX coverage
- deeper history
- smart-money/entity enhancement
- composite market/reference prices
- richer DeFi/on-chain sources
- material-change engine sophistication
- automated source qualification

## P2 — buy only after measured need
- premium historical L2/L3
- premium labels
- direct low-latency institutional feeds
- contractual enterprise SLA
- premium bulk archives

---

# 56. Final Answer to the 13 Operational Questions

1. **Where does data come from?**  
   Direct official exchanges, blockchains/RPC, DeFi/protocol sources, official macro/regulatory sources, qualified aggregators, news/event sources, and optionally user-authorized portfolio sources.

2. **Is using free alternatives dangerous?**  
   Not by itself. The danger is unlicensed use, single-source dependence, no SLA/SLO, insufficient history, poor quality and no failover.

3. **Will refusing to pay stop the model?**  
   It must not. Core operation continues from qualified public/free/owned sources; capabilities whose truth cannot be supported must degrade/abstain until the missing source/history/license exists.

4. **Update speed?**  
   Source-appropriate: event-driven WebSockets for market microstructure; block/event driven on-chain; release/event driven macro/regulatory; slower source cadence for DeFi aggregates. Show freshness explicitly.

5. **Where did a displayed fact come from?**  
   Provenance and lineage must answer exactly.

6. **Normalized?**  
   Mandatory for material multi-source data.

7. **Historical depth?**  
   Methodology-specific and enforced before Grade/Simulation. Capture high-resolution history from day one.

8. **L2/L3?**  
   L2 mandatory for execution-sensitive calculations where available. L3 only where methodology genuinely requires it and source supports it.

9. **SLA?**  
   External SLA only if contractual. Internal SLO mandatory for every critical source class.

10. **Provenance?**  
    Mandatory.

11. **Methodology?**  
    Mandatory and versioned.

12. **Reliability?**  
    Continuously measured per source and wired into decision safety.

13. **Auditability?**  
    Critical decisions must be reproducible/replayable from source evidence.

---

# 57. Final Recommendation

**EXECUTE.**

The proposal should be implemented, but not as a “data integrations project”.

The institutional target is:

# BLACKDARK Data Truth Fabric

feeding:

# BLACKDARK Decision Truth System

The differentiator is not owning more APIs than competitors.

It is the ability to tell the user, continuously and audibly:

> **What changed, whether the data is trustworthy, whether an apparent opportunity survives real costs and execution, what can hurt the user, what BLACKDARK rejected, and when there is not enough evidence to make a decision.**

---

# 58. Authoritative Public Research References Used for This Specification

1. NIST AI RMF 1.0 — https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-ai-rmf-10
2. ISO/IEC 42001:2023 — https://www.iso.org/standard/42001
3. BCBS 239 — https://www.bis.org/publ/bcbs239.pdf
4. EU AI Act Regulation (EU) 2024/1689, Article 10 — https://eur-lex.europa.eu/eli/reg/2024/1689/oj
5. FTC Safeguards Rule — https://www.ftc.gov/legal-library/browse/rules/safeguards-rule
6. Coinbase Advanced Trade WebSockets — https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/websocket/websocket-overview
7. Coinbase Exchange WebSocket channels / L2/L3 — https://docs.cdp.coinbase.com/exchange/websocket-feed/channels
8. Bybit V5 public WebSocket/order book — https://bybit-exchange.github.io/docs/v5/websocket/public/orderbook
9. OKX API/WebSocket guide — https://www.okx.com/docs-v5
10. Binance WebSocket market streams — https://developers.binance.com/
11. Ethereum JSON-RPC — https://ethereum.org/developers/docs/apis/json-rpc/
12. FRED API — https://fred.stlouisfed.org/docs/api/fred/
13. SEC EDGAR public APIs — https://www.sec.gov/search-filings/edgar-application-programming-interfaces
14. Dune API rate limits/SLA documentation — https://docs.dune.com/api-reference/overview/rate-limits
15. DefiLlama API/terms — https://defillama.com/docs/api and https://defillama.com/terms

---

# 59. Cursor Final Execution Rule

Cursor must treat this file as a complete governing specification.

It must:
- perform repository-wide source-driven audit first
- map existing BLACKDARK data code to every requirement
- REUSE/IMPROVE existing canonical owners instead of duplicating
- build all locally-buildable missing requirements
- wire them into real runtime and Decision Truth paths
- test semantics, failure, recovery, provenance, history and UI
- perform a second complete source pass
- claim engineering closure only when all locally-buildable gap arrays are empty

Final allowed engineering statement:

> **All locally-buildable requirements in BLACKDARK Institutional Data Intelligence, Governance & Operations Specification v1 are implemented, integrated into intended runtime paths, regression-verified and reconciled against the governing source. No known local material source-ingestion, normalization, quality, freshness, provenance, methodology, history, reliability, auditability, resilience, Decision Truth integration, or user-facing data-truth gaps remain. Production/live, licensing-contractual and external legal verification remain separately gated and have not been falsely claimed.**
