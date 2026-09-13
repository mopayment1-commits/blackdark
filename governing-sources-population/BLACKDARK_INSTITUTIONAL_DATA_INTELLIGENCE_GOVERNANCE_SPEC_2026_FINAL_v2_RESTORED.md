# BLACKDARK — Institutional Data Intelligence & Governance Specification 2026 — Final v1

**Status:** Governing Source of Truth (SSOT) for data acquisition, ingestion, normalization, quality, lineage, historical depth, real-time operation, resilience, governance, methodology, and user-facing Decision Truth inputs.

**Strategic objective:** BLACKDARK must not merely collect crypto data. It must maintain an auditable, multi-source, freshness-aware, normalized, resilient data fabric capable of feeding the Decision Truth System with sufficiently complete, timely, reliable and explainable evidence — and must degrade or abstain when that standard is not met.

---

# 0. Final institutional judgement

The correct architecture is **not**:

`One API → database → dashboard`

It is:

```text
SOURCE REGISTRY
→ MULTI-SOURCE ACQUISITION
→ RAW IMMUTABLE LANDING
→ SCHEMA / IDENTITY NORMALIZATION
→ QUALITY + FRESHNESS + RELIABILITY GATES
→ RECONCILIATION / CONFLICT RESOLUTION
→ CANONICAL DATA PRODUCTS
→ HISTORICAL / REPLAY STORE
→ DERIVED METRICS + METHODOLOGY
→ DECISION TRUTH INPUTS
→ PROVENANCE / LINEAGE / AUDIT
→ USER-FACING FRESHNESS + EVIDENCE
```

No critical decision may depend blindly on one free third-party source.

Free/open/public sources are allowed and should be maximized for cost efficiency, but source criticality, legal redistribution rights, rate limits, historical coverage, latency and reliability must determine whether a source can be Primary, Secondary, Fallback or Discovery-only.

---

# 1. Five-level review standard

## Level 1 — Source truth
Every source must have documented identity, owner, endpoint/feed, authentication model, terms/licence/redistribution status, data scope, update behavior, historical availability and known limits.

## Level 2 — Technical truth
Verify transport, rate limits, sequencing, snapshots/deltas, timestamps, retries, reconnect behavior, checksums where available, schema versioning and failure modes.

## Level 3 — Data truth
Verify normalization, identity mapping, units, precision, completeness, freshness, consistency, anomaly rules, reconciliation and data quality.

## Level 4 — Decision truth
Verify whether the data is sufficient for the specific downstream claim: Net-Edge, execution feasibility, risk, grade, simulation, smart-money context, stress testing or user alert.

## Level 5 — Governance / audit truth
Verify provenance, lineage, methodology, retention, access, privacy, vendor risk, auditability, evidence replay and operational SLOs.

---

# 2. Non-negotiable principles

## DATA-001 — Source registry
Maintain one canonical machine-readable Source Registry.

For every source record:
- source_id
- provider
- source_type
- domain
- official/public/derived
- primary/secondary/fallback/discovery role
- auth type
- credential owner
- endpoint/feed
- asset/chain/venue coverage
- update mechanism
- expected cadence
- provider SLA if contractual
- internal SLO
- rate limits / quotas
- historical depth
- L1/L2/L3 capability
- redistribution/licensing status
- data classification
- cost/tier
- health status
- methodology/reference URL/version
- last review date

## DATA-002 — No undocumented source
No source may feed a critical user-facing decision unless present in the Source Registry.

## DATA-003 — Critical source independence
Critical decision paths must not rely on a single fragile free source when a second independent route is technically available.

## DATA-004 — Source role classification
Every source must be explicitly classified:
- PRIMARY
- SECONDARY
- FALLBACK
- DISCOVERY_ONLY
- VALIDATION_ONLY
- DERIVED_INTERNAL

## DATA-005 — Source admission
A provider is admitted to a critical path only after technical, legal/licensing, security, quality and operational assessment.

---

# 3. Required data domains

## DATA-006 — CEX market data
Acquire as relevant:
- ticker
- best bid/ask
- trades
- OHLCV
- order-book snapshots
- incremental depth updates
- funding
- open interest
- mark/index price
- liquidations
- instrument metadata
- trading status
- deposit/withdrawal status where available
- fees
- maintenance/status signals

## DATA-007 — DEX / on-chain market data
Acquire as relevant:
- pools
- swaps/trades
- reserves/liquidity
- OHLCV
- TVL
- fees/revenue
- price impact
- routing state
- gas/network fees
- bridge state
- token/pool metadata

## DATA-008 — Blockchain / network data
Acquire:
- blocks
- transactions
- fees
- mempool/network congestion where defensible
- validator/network status where relevant
- chain finality indicators
- addresses/entities required for product scope

## DATA-009 — Derivatives data
Acquire:
- funding
- basis
- open interest
- liquidation
- mark/index
- term structure where available
- perp positioning inputs
- options IV/skew/term structure where supported

## DATA-010 — Portfolio / account context
Only with authorized user connection:
- balances
- positions
- cost basis where available
- realized/unrealized PnL inputs
- exposure
- account/venue status

Public market data must remain logically separated from private user/account data.

## DATA-011 — Smart-money / entity intelligence
Acquire only with provenance and confidence:
- wallet activity
- entity labels
- clusters
- holdings
- flows
- historical holdings
- related-wallet evidence
- label confidence/source

## DATA-012 — DeFi intelligence
Acquire:
- TVL
- yields
- fees/revenue
- stablecoin supply/distribution
- bridge flows
- protocol security/hack history where applicable
- token unlock/emission data
- treasury/fundraising/RWA/ETF context where product-relevant

## DATA-013 — Macro / reference data
Acquire where decision-relevant:
- FX
- rates
- benchmark/reference prices
- calendar/event data
- ETF flows
- macro indicators

Never fabricate unsupported high-frequency macro freshness.

## DATA-014 — News/event/context data
Use for context, not unquestioned causal truth.
Record publisher/source, published_at, observed_at and extraction methodology.

## DATA-015 — Internal outcome data
Maintain internal:
- decision ledger
- prediction ledger
- outcome ledger
- calibration
- rejection statistics
- source reliability
- incident/failure evidence
- methodology versions

This internal evidence is a strategic asset.

---

# 4. Authentication, API keys and account activation

## DATA-016 — Public feeds first where sufficient
Use official unauthenticated/public market streams when they provide required data and terms permit the use.

## DATA-017 — Authenticated feeds only when required
Use API keys/signatures for:
- provider APIs that require keys
- account/user streams
- private portfolio/account data
- paid/entitled endpoints
- higher-rate institutional feeds

## DATA-018 — Secrets management
All credentials:
- server-side only
- environment/secret manager
- never hard-coded
- never exposed to browser
- least privilege
- rotatable
- auditable

## DATA-019 — Separate environments
Separate:
- test/sandbox keys
- production/live keys
- user-specific credentials
- provider service credentials

## DATA-020 — Credential health
Monitor:
- expiration
- revocation
- permission errors
- quota
- rate-limit state
- authentication failures

---

# 5. Real-time update architecture

## DATA-021 — Event-driven real-time
For fast-moving market data, prefer official WebSocket/event streams over repeated REST polling where supported.

## DATA-022 — REST role
REST is used for:
- bootstrap snapshots
- metadata/reference
- historical/backfill
- reconciliation
- periodic low-frequency data
- recovery after stream gaps

## DATA-023 — Snapshot + delta
Order-book consumers must implement correct:
- initial snapshot
- ordered deltas
- sequence tracking
- gap detection
- resnapshot/recovery
- checksum verification where provider exposes one

## DATA-024 — Reconnect resilience
Implement:
- heartbeat/ping handling
- bounded reconnect
- exponential backoff + jitter
- subscription replay
- stale state during outage
- no silent continuation after sequence gap

## DATA-025 — Cadence by data class
No single global refresh interval.

Suggested operating classes:
- T0 ultra-fast: trades/order-book/market microstructure — event-driven/sub-second to seconds according to source
- T1 fast: prices/funding/liquidations/venue health — seconds
- T2 near-real-time: on-chain pools/flows/network — seconds to minutes
- T3 analytical: TVL/yields/smart-money aggregates — minutes to hours according to source methodology
- T4 reference: metadata/methodology/vendor/legal — hours/daily/on-change
- T5 daily research: briefs/calibration/history — scheduled plus event-triggered invalidation

Actual SLO must be defined per dataset, not copied blindly from these ranges.

## DATA-026 — Freshness state
Canonical:
- LIVE
- NEAR_LIVE
- DELAYED
- STALE
- CACHED
- PARTIAL
- UNKNOWN

## DATA-027 — Freshness metadata
Critical records expose:
- source_timestamp
- observed_at
- ingested_at
- processed_at
- last_successful_update
- age_seconds
- freshness_state

---

# 6. Normalization

## DATA-028 — Canonical identity
Never normalize only by ticker symbol.

Use stable canonical IDs for:
- asset
- chain
- contract
- venue
- instrument
- market
- pool
- wallet/entity

## DATA-029 — Symbol ambiguity protection
BTC-like symbols, wrapped assets, bridged assets, derivatives and duplicate tickers require explicit identity mapping.

## DATA-030 — Canonical units
Define canonical:
- currency
- quote/base
- quantity
- notional
- percentage
- APR/APY
- timestamps
- decimals/precision
- chain units
- fee units

## DATA-031 — Decimal integrity
Financial values use Decimal/fixed precision where exactness matters; avoid uncontrolled binary-float semantics at financial boundaries.

## DATA-032 — Schema contracts
Each canonical dataset has versioned schema contract with:
- required fields
- nullable fields
- types
- units
- constraints
- semantics
- compatibility rules

## DATA-033 — Normalization trace
Preserve raw field → normalized field mapping.

---

# 7. Raw, canonical and derived storage

## DATA-034 — Immutable raw landing
Preserve raw provider payload/evidence where licensing and privacy allow, or retain cryptographic reference/hash plus replay-enabling metadata where raw retention is restricted.

## DATA-035 — Canonical store
Normalized data is stored separately from raw evidence.

## DATA-036 — Derived metric store
Derived outputs must never overwrite raw/canonical source evidence.

## DATA-037 — Time-series/history store
Historical storage supports:
- point-in-time replay
- backtests
- incident reconstruction
- methodology comparison
- outcome calibration

## DATA-038 — Bitemporal/knowledge-time semantics where material
For decision-critical datasets distinguish, where needed:
- event/source time
- ingestion/knowledge time
so historical replay does not accidentally use information not yet known at the original decision time.

---

# 8. Historical depth

## DATA-039 — Dataset-specific historical depth
Historical depth is not one global number.

Maintain for every dataset:
- earliest_available_source_time
- earliest_locally_stored_time
- gaps
- resolution
- schema/methodology changes
- backfill status

## DATA-040 — Grade sufficiency
No Strategy Grade / calibration / simulation claim unless historical depth and sample size meet the methodology-specific threshold.

## DATA-041 — Look-ahead protection
Backtests/replay must use only information available as-of the historical decision time.

## DATA-042 — Survivorship/change protection
Track:
- delisted instruments
- renamed assets
- contract migrations
- provider methodology changes
- venue shutdowns
where relevant to historical analysis.

---

# 9. L1 / L2 / L3 policy

## DATA-043 — L1
L1/best bid-ask/ticker may support:
- broad discovery
- simple monitoring
- non-execution-sensitive views

It is insufficient for execution-realism claims that depend on depth.

## DATA-044 — L2
L2 aggregated price-level order books are mandatory for decision paths requiring:
- slippage
- market depth
- capacity
- fill feasibility approximation
- microstructure-aware Net-Edge

where the venue/source supports L2.

## DATA-045 — L3
L3/order-level data is not a universal requirement.

Require it only where:
- a specific methodology depends on individual order identity/queue dynamics
- source legally/technically provides it
- incremental decision value justifies cost/storage/complexity

Do not label L2 as L3.

## DATA-046 — Order-book historical depth
If historical L2/L3 is required for simulation, it must be captured locally from live feeds or obtained from a source that explicitly provides historical depth. Current book snapshots alone are not historical depth.

---

# 10. Data quality gates

## DATA-047 — Required dimensions
Measure at minimum:
- completeness
- timeliness
- accuracy/validation
- consistency
- integrity
- provenance
- historical sufficiency
- availability
- reconciliation status

## DATA-048 — Quality state
Canonical:
- COMPLETE
- PARTIAL
- CONFLICTING
- INSUFFICIENT
- SUSPECT
- UNVERIFIED

## DATA-049 — Quality rules
Maintain a versioned rule inventory:
- range checks
- null checks
- monotonicity/sequence checks
- cross-source variance
- stale thresholds
- schema drift
- duplicate detection
- outlier logic
- reconciliation rules

## DATA-050 — Decision admission effect
Material quality failure must propagate into Decision Truth admission:
- DEGRADE
- ABSTAIN
- REJECT
- UNAVAILABLE
as appropriate.

---

# 11. Multi-source reconciliation

## DATA-051 — Independent corroboration
For critical reference prices/market states, use independent corroboration when feasible.

## DATA-052 — Conflict state
Do not silently average conflicting sources.

Record:
- conflicting_sources
- variance
- selected_source
- selection_method
- reason
- confidence impact

## DATA-053 — Source priority
Priority is dataset-specific and considers:
- directness/originality
- freshness
- completeness
- historical reliability
- methodology
- venue relevance
- SLA/SLO
- licensing

Paid ≠ automatically correct; free ≠ automatically unreliable.

---

# 12. SLA, SLO and operational reliability

## DATA-054 — Provider SLA vs internal SLO
Distinguish:
- contractual provider SLA
- provider documented limits
- BLACKDARK internal SLO
- measured actual reliability

## DATA-055 — Internal SLO per critical dataset
Define:
- availability target
- freshness target
- completeness target
- max tolerated gap
- recovery target
- error budget
- alert threshold

## DATA-056 — No invented SLA
If a free/public feed has no contractual SLA, record `PROVIDER_SLA=NONE`, not an assumed percentage.

## DATA-057 — Source health score
Track measured:
- success rate
- latency
- staleness
- schema errors
- gap rate
- reconciliation disagreement
- incident count

## DATA-058 — Automatic source downgrade
Source reliability degradation can change source role/weight and trigger fallback/degraded behavior.

---

# 13. Provenance and lineage

## DATA-059 — Provenance
Every critical output must be traceable to source evidence.

Minimum:
- source_id
- provider
- endpoint/feed
- source_timestamp
- observed_at
- ingestion event
- raw evidence/hash
- schema version

## DATA-060 — End-to-end lineage
For each material decision:
raw source
→ normalization
→ transformations
→ quality gates
→ derived metric
→ methodology version
→ decision contract
→ user-facing output

## DATA-061 — W3C-style provenance semantics
Use entity/activity/agent style concepts or equivalent internal model for interoperable provenance.

## DATA-062 — User-facing provenance
Critical Decision Truth output exposes concise:
- source/evidence class
- freshness
- methodology/version
- limitations
with drill-down to full evidence trail.

---

# 14. Methodology governance

## DATA-063 — Methodology card
Every material derived metric has:
- definition
- equation/logic
- required inputs
- exclusions
- assumptions
- thresholds
- limitations
- validation
- version
- effective date
- owner

## DATA-064 — Methodology change control
No silent formula changes.

Changes require:
- new version
- effective timestamp
- migration/comparability note
- regression validation
- audit event

## DATA-065 — Provider methodology dependency
If a derived metric depends on vendor methodology, record vendor methodology/version/reference where available.

---

# 15. Auditability

## DATA-066 — Immutable material audit trail
Audit:
- source onboarding/removal
- key/config changes
- schema changes
- normalization changes
- methodology changes
- quality rule changes
- manual overrides
- fallback activation
- decision-data corrections

## DATA-067 — Replay
A material historical decision must be reconstructable from retained evidence to the extent permitted by source licensing/privacy.

## DATA-068 — Manual intervention
Any manual correction/override requires:
- actor
- time
- reason
- before/after
- approval where appropriate

---

# 16. Reliability and degradation

## DATA-069 — No platform-wide failure from one source
One source outage must not silently kill unrelated capabilities.

## DATA-070 — Fallback matrix
For every critical dataset define:
PRIMARY → SECONDARY → CACHED/DEGRADED → ABSTAIN/UNAVAILABLE.

## DATA-071 — No stale masquerading as live
Cached/stale data can be shown only with explicit freshness state.

## DATA-072 — Insufficient input abstention
If required inputs for Net-Edge/Risk/Grade/Decision Truth are insufficient, the system must abstain/reject rather than fill unknowns with deceptive zeros.

## DATA-073 — Circuit breakers
Unhealthy upstream providers must be isolated with bounded retry/circuit behavior.

---

# 17. Free-source strategy and paid-dependency policy

## DATA-074 — Free-first, not free-only
BLACKDARK should maximize:
- direct official exchange public WebSockets
- public blockchain/RPC data where sufficient
- open/public APIs
- self-derived metrics
- internally accumulated history

But it must not architect critical truth around free-tier promises that have no SLA or adequate quota/history.

## DATA-075 — Paid source trigger
A paid provider becomes justified when a locally measured gap remains in one or more of:
- latency
- coverage
- historical depth
- redistribution rights
- labelled/entity intelligence
- API quota
- reliability/SLA
- support
- data quality
and that gap materially affects a product promise.

## DATA-076 — No-money mode
If no paid source is available:
- degrade the affected capability
- use alternative independent source where lawful/valid
- mark lower evidence class
- restrict or abstain
- never fabricate equivalent coverage

The entire platform should not be blocked unless the unavailable data is truly essential to the platform’s core promise.

---

# 18. Vendor risk / legal / privacy

## DATA-077 — Licensing and redistribution
For every source, determine:
- API terms
- caching rights
- historical storage rights
- redistribution/display rights
- derived-data rights
- attribution obligations

## DATA-078 — Third-party risk
Assess critical vendors for:
- security
- availability
- business continuity
- incident communication
- concentration risk
- portability/exit

## DATA-079 — GLBA applicability decision
Document legal determination of whether BLACKDARK is a covered financial institution/service provider under applicable GLBA/FTC scope.

If applicable, implement required safeguards and service-provider oversight.

## DATA-080 — GDPR/privacy separation
Personal/account/wallet-linked user data is governed separately from public market data:
- purpose
- minimization
- access
- retention
- deletion/export rights as applicable
- security controls

## DATA-081 — AI governance
Use NIST AI RMF / ISO/IEC 42001 as governance frameworks for AI-assisted decision outputs.

## DATA-082 — EU AI Act conditionality
Do not claim Article 10 is automatically applicable to all BLACKDARK functionality.
Determine legal classification and apply high-risk requirements only if the specific system/use falls within scope.

---

# 19. Source strategy by category

## Direct venue / exchange sources
Preferred PRIMARY for venue-specific real-time truth where technically available:
- official exchange WebSocket market feeds
- official REST snapshot/reference endpoints
- official venue status/metadata APIs

Examples to evaluate per supported venue:
- Binance
- Coinbase
- Kraken
- OKX
- Bybit
- Bitstamp
- Gemini
- Gate.io
- KuCoin
- Crypto.com
- Bitfinex
- other supported venues

Each connector must be individually validated; do not infer identical semantics.

## Aggregators
Use primarily for breadth, discovery, metadata, cross-checking and historical/reference data:
- CoinGecko
- CoinMarketCap
- equivalent validated aggregators

Not automatically execution-grade.

## DeFi
- direct protocol/on-chain reads where feasible
- DefiLlama for broad protocol/TVL/yields/fees/context
- DEX-specific APIs/indexers
- blockchain nodes/indexers

## On-chain / smart money
- self-derived chain data
- validated indexers
- Nansen or equivalent when paid labelled intelligence is justified
- internal wallet/entity models with confidence/provenance

## Institutional on-chain metrics
- self-derived metrics where feasible
- Glassnode or comparable source when methodology/history/coverage creates sufficient value

---

# 20. Specific operating answers to the 13 user questions

## Q1 — Where does data come from and who is connected?
From a governed portfolio of direct exchanges, DEX/on-chain feeds, aggregators, DeFi datasets, blockchain/indexer sources, smart-money/entity sources, macro/reference/event sources, plus internally derived and user-authorized account data. Public market feeds may require no key; private/account or premium APIs require API keys/signatures and account activation.

## Q2 — Is reliance on free alternatives dangerous?
**Free is not the risk. Single-source dependency, absent SLA, insufficient quota/history, unclear licence and unmeasured reliability are the risk.**

## Q3 — Will no payment block the model?
Not necessarily. Build a free-first multi-source MVP with transparent degradation. Some institutional promises may remain unavailable/degraded until adequate data rights/coverage/SLA are obtained.

## Q4 — Update speed
Per dataset SLO; event-driven WebSocket for microstructure, slower scheduled/event-triggered cadence for analytical/reference data.

## Q5 — Where did data come from?
Every critical output must expose provenance and source lineage.

## Q6 — Is it normalized?
All data entering canonical decision paths must be normalized by versioned contracts.

## Q7 — Historical depth?
Tracked per dataset; required for Grade/backtest/calibration claims.

## Q8 — L2/L3?
L2 required where depth/slippage/capacity matters. L3 only where methodology truly requires it and source provides it.

## Q9 — SLA?
Provider SLA if contractual; internal SLO always for critical datasets. Never invent SLA for free feeds.

## Q10 — Provenance?
Mandatory.

## Q11 — Methodology?
Mandatory for every material derived metric.

## Q12 — Reliability?
Measured continuously and used in source weighting/fallback.

## Q13 — Auditability?
Mandatory end-to-end for material decisions.

---

# 21. User-facing differentiator — Live Decision Pulse

The first surface should not be a price dashboard.

Create a **Live Decision Pulse** powered by Decision Truth.

At any moment show:

1. **Capital State**
   - portfolio risk / exposure if connected
   - risk budget status

2. **What Changed**
   - maximum three material changes
   - each with evidence/freshness

3. **Best Verified Opportunity**
   - not largest raw spread
   - highest admitted opportunity after cost, execution, capacity, risk and evidence

4. **What BLACKDARK Rejected**
   - visible count / top rejected apparent opportunity
   - Why NOT

5. **Main Pre-Impact Risk**
   - venue/stablecoin/liquidity/portfolio threat before material impact

6. **Data Confidence / Market Truth Status**
   - LIVE / DEGRADED / PARTIAL / CONFLICTING / ABSTAINING

7. **Decision Change**
   - what materially changed since the user last looked

8. **Evidence Trail**
   - sources, timestamps, freshness, methodology, limitations

This is not a generic “morning brief”; it is a continuously recomputed truth surface.

---

# 22. Why this can be a real differentiator

The moat is not the raw data source because competitors can buy the same feeds.

The differentiator is the integrated transformation:

```text
MULTI-SOURCE DATA
→ QUALITY
→ FRESHNESS
→ EXECUTION REALITY
→ NET ECONOMIC TRUTH
→ PORTFOLIO PRE-IMPACT
→ EVIDENCE
→ ABSTENTION / REJECTION
→ EXPLANATION
→ OUTCOME CALIBRATION
```

The strongest user-facing moments are:

- “The raw opportunity looked +4.7%; BLACKDARK rejected it after cost and execution reality.”
- “This looks profitable alone, but breaches your portfolio risk envelope.”
- “NO DECISION — the sources materially conflict.”
- “Decision changed since your last visit, and here is exactly why.”
- “Here is the complete evidence and data lineage behind this result.”

---

# 23. Rejected defects from Recommendation 1

The following must be removed or corrected:

1. “Primary paid/reliable is required for every critical path” — too absolute. Direct official public exchange feeds can be primary if measured quality and rights are sufficient.
2. “Free source = secondary only” — false as a universal rule.
3. “L1 + derivatives is enough for most retail” — cannot be universalized; execution-sensitive Net-Edge often needs L2 depth.
4. “EU AI Act Art.10” as a blanket BLACKDARK requirement — conditional on legal classification/scope.
5. “GLBA must apply” — must be legally determined, not assumed.
6. “SLA required from every provider” — impossible for many public/free sources; internal SLO is mandatory, provider SLA only when contractual.
7. “Historical depth sufficient for Grade” without defining dataset/methodology threshold — insufficient.
8. Generic `Source → Ingest → Normalize → Quality → Metric → Decision` is missing raw immutable evidence, reconciliation, versioning, replay and knowledge-time controls.
9. No licensing/redistribution/storage-rights gate — material omission.
10. No source concentration/exit plan — material omission.
11. No snapshot/delta/order-book sequence recovery contract — material omission.
12. No schema drift/version compatibility gate — material omission.
13. No bitemporal/as-known-at replay control — material omission for serious backtesting.
14. No explicit source reliability measurement/automatic downgrade.
15. No decision-level multi-source conflict state.
16. No data-retention / privacy classification policy.
17. No data incident / correction propagation policy.
18. No cost/usage budget governance for API quotas.
19. No explicit anti-lookahead / survivorship controls.
20. No user-facing source/evidence transparency contract.

---

# 24. New mandatory institutional additions

## DATA-083 — Schema drift detection
Automatically detect provider field/type/enum changes.

## DATA-084 — Contract tests per provider
Run connector contract tests against representative payloads and version assumptions.

## DATA-085 — Quota governance
Monitor API usage and forecast exhaustion.

## DATA-086 — Cost budget
Maintain cost per provider/dataset and cost-per-decision/output where meaningful.

## DATA-087 — Source concentration risk
Measure dependence on each vendor/provider.

## DATA-088 — Provider exit plan
Critical third-party source must have replacement/degradation plan.

## DATA-089 — Correction propagation
If historical/provider data is corrected, identify affected derived metrics/decisions and recompute or mark superseded.

## DATA-090 — Data incident ledger
Record material data outages, corruption, schema breakages and decision impact.

## DATA-091 — Data retention matrix
Define retention by data class and legal/licensing constraints.

## DATA-092 — Access-control matrix
Define who/service can read/write raw, canonical, derived, private and audit data.

## DATA-093 — Encryption/security
Protect credentials and sensitive user data at rest/in transit; apply integrity controls to material evidence.

## DATA-094 — Backup/restore
Critical canonical/history/ledger data requires tested backup/restore appropriate to deployment.

## DATA-095 — Clock discipline
All canonical event/ingestion/audit timestamps must use existing global UTC-aware time authority.

## DATA-096 — Data contract ownership
Each canonical dataset and methodology has a named technical/business owner role.

## DATA-097 — Data-quality SLO
Every critical dataset has quantitative quality/freshness thresholds and escalation.

## DATA-098 — Observability
Metrics:
- ingest_success
- ingest_latency
- source_age
- schema_error
- sequence_gap
- reconciliation_conflict
- stale_duration
- fallback_activation
- decision_abstention_due_to_data
- quota_remaining

## DATA-099 — Synthetic/fault testing
Test:
- source timeout
- malformed payload
- schema change
- duplicate
- out-of-order
- missed sequence
- stale source
- conflicting source
- quota exhaustion
- auth revocation
- clock skew
- corrupt backfill

## DATA-100 — Full local closure
No PASS_ENGINEERING_DATA unless all locally-buildable DATA-001→DATA-100 requirements are accounted for, implemented, integrated and tested, with exact live/external gates separated.

---

# 25. Final acceptance contract

Required before local engineering closure:

```text
SOURCE_REGISTRY_PASS=true
MULTI_SOURCE_STRATEGY_PASS=true
CRITICAL_SOURCE_CONCENTRATION_PASS=true
SOURCE_ADMISSION_PASS=true
AUTH_SECRET_MANAGEMENT_PASS=true
REALTIME_STREAMING_PASS=true
SNAPSHOT_DELTA_RECOVERY_PASS=true
DATASET_CADENCE_SLO_PASS=true
NORMALIZATION_CONTRACT_PASS=true
CANONICAL_IDENTITY_PASS=true
SCHEMA_VERSIONING_PASS=true
RAW_EVIDENCE_PASS=true
CANONICAL_STORE_PASS=true
HISTORICAL_DEPTH_REGISTRY_PASS=true
POINT_IN_TIME_REPLAY_PASS=true
ANTI_LOOKAHEAD_PASS=true
L2_POLICY_PASS=true
L3_POLICY_PASS=true
QUALITY_GATE_PASS=true
MULTI_SOURCE_RECONCILIATION_PASS=true
PROVIDER_SLA_INTERNAL_SLO_SEPARATION_PASS=true
SOURCE_RELIABILITY_PASS=true
PROVENANCE_PASS=true
END_TO_END_LINEAGE_PASS=true
METHODOLOGY_GOVERNANCE_PASS=true
AUDITABILITY_PASS=true
FALLBACK_DEGRADE_ABSTAIN_PASS=true
LICENSING_REDISTRIBUTION_PASS=true
VENDOR_RISK_PASS=true
PRIVACY_SEPARATION_PASS=true
SCHEMA_DRIFT_PASS=true
QUOTA_COST_GOVERNANCE_PASS=true
PROVIDER_EXIT_PLAN_PASS=true
CORRECTION_PROPAGATION_PASS=true
DATA_INCIDENT_LEDGER_PASS=true
RETENTION_ACCESS_CONTROL_PASS=true
BACKUP_RESTORE_PASS=true
DATA_OBSERVABILITY_PASS=true
DATA_FAULT_INJECTION_PASS=true
LIVE_DECISION_PULSE_INTEGRATION_PASS=true
DECISION_TRUTH_DATA_INTEGRATION_PASS=true

SOURCE_REQUIREMENTS_ACCOUNTED_FOR=100%
KNOWN_LOCAL_DATA_GAPS=[]
KNOWN_LOCAL_DATA_DEFECTS=[]
KNOWN_LOCAL_DATA_INTEGRATION_GAPS=[]
KNOWN_LOCAL_DATA_TEST_GAPS=[]
LOCAL_BUILDABLE_DATA_REQUIREMENTS_REMAINING=0
PARTIALLY_IMPLEMENTED_LOCAL_DATA_REQUIREMENTS=0
UNIMPLEMENTED_LOCAL_DATA_REQUIREMENTS=0
UNVERIFIED_LOCAL_DATA_REQUIREMENTS=0

PASS_ENGINEERING_DATA=true
READY_FOR_INTENDED_LOCAL_USE=true
PASS_LIVE_NOT_CLAIMED=true
```

Production/live claims require measured production evidence and may not be inferred from local tests.

---

# 26. Final implementation decision

**IMPLEMENT.**

But implement it as an institutional **Data Truth Fabric**, not as a collection of API integrations.

The most valuable strategic asset is not a paid feed. It is the combination of:
- independent direct source acquisition
- accumulated historical evidence
- normalization
- source reliability history
- point-in-time replay
- methodology
- Decision Truth integration
- rejection/abstention
- outcome calibration
- auditable provenance

Over time this creates an internal data/evidence asset that becomes progressively harder to reproduce by simply subscribing to the same external APIs.

---

# 27. Reference framework basis

This specification is designed to align, proportionately and where applicable, with:
- BCBS 239 / Basel risk-data principles (accuracy/integrity, completeness, timeliness, adaptability, governance, reconciliation, validation, service-level standards)
- January 2026 Basel Committee implementation observations emphasizing governance, lineage and timely/accurate/complete risk data
- W3C PROV provenance model concepts
- NIST AI Risk Management Framework trustworthiness characteristics
- ISO/IEC 42001:2023 AI management-system governance
- GDPR/privacy obligations where applicable
- FTC GLBA Safeguards Rule only if legal applicability is determined
- EU AI Act data-governance requirements only where the specific AI system/use is legally in scope
- official provider documentation and contractual terms for each data source


---

# 28. Governing Recovery Addendum — Restored Decisions from Prior Canonical Discussion

**Status:** Mandatory. This addendum restores decisions that were present in the prior canonical discussion but were not stated explicitly enough in Final v1. It is part of the SSOT and MUST be implemented together with DATA-001→DATA-100. If wording conflicts, the stricter evidence-backed requirement applies.

## RESTORE-001 — Do not integrate 100 sources at once
BLACKDARK MUST NOT attempt to onboard/integrate the full ~100-source universe in one implementation wave. Doing so increases integration failure surface, operational complexity, maintenance burden and cost without proportional decision value. Source expansion MUST be staged and evidence-driven.

## RESTORE-002 — Three-stage source execution strategy
### Phase I — Institutional Core
Target approximately **25–35 highest-value sources/routes**, selected by decision criticality and independence, including as applicable:
- major CEX direct official feeds
- major DEX / perp-DEX routes
- direct chain/RPC/indexer paths
- CoinGecko / CoinMarketCap or equivalent primarily as fallback/discovery/reference/cross-check, not automatically execution-grade
- FRED / Federal Reserve / ECB or equivalent official macro sources
- SEC / CFTC or equivalent official regulatory sources
- licensed news/reference source or lawful validated alternative where required

Phase I is complete only when the selected core sources are normalized, quality-gated, reconciled, freshness-aware, observable, historically governed and actually wired into intended decision paths.

### Phase II — Intelligence Expansion
Expand only after Phase I engineering closure into:
- institutional on-chain feeds where justified
- options / volatility intelligence
- DeFi fundamentals
- broader global macro
- energy / commodities context where decision-relevant
- sanctions / geopolitical / event intelligence where lawful and methodologically defensible

### Phase III — Data Moat
Build BLACKDARK-owned defensibility through:
- proprietary derived indicators/datasets
- historical data lake / evidence lake
- entity graph
- event graph
- source reliability history
- cross-venue liquidity map
- internally accumulated point-in-time datasets
- proprietary normalized/derived data products

The strategic moat is NOT the statement “BLACKDARK has 100 APIs.” The moat is the governed transformation of conflicting multi-source evidence into auditable Financial/Decision Truth.

## RESTORE-003 — Data Trust Engine observation contract
Every material observation entering critical decision paths MUST carry, directly or through canonical equivalent fields:
- source
- source_class / source_role
- instrument / asset identity
- venue / chain where applicable
- event_time
- received_time / observed_at
- ingestion_time where distinct
- latency_ms where meaningful
- data_type
- raw_value or raw evidence reference
- normalized_value where applicable
- freshness state / age
- quality_score or equivalent quality evidence
- schema/version identity
- provenance/evidence reference

Source reliability/quality scoring must consider, as applicable:
- freshness
- directness
- historical accuracy
- cross-source agreement
- completeness
- latency
- anomaly/error rate

No source is “always trusted.” Reliability must be measured and allowed to change over time.

## RESTORE-004 — Explicit source-conflict decision rules
At minimum, critical source handling MUST implement equivalent behavior to:
- `Source A fails → use validated B/fallback when eligible`
- `A and B materially disagree → CONFLICT/QUARANTINE; do not silently average into certainty`
- `stale beyond dataset threshold → REJECT/DEGRADE/ABSTAIN according to decision need`
- `material outlier/anomaly → quarantine/investigate; do not silently promote to canonical truth`
- `single-source-only critical evidence → explicit concentration/confidence penalty or abstention according to policy`

These rules must be represented in code/policy, tested, observable and traceable.

## RESTORE-005 — Canonical reconciliation layer
The intended data path MUST contain a real reconciliation/consensus function between quality-gated normalized inputs and canonical decision state. Conceptually:

`Multi-source normalized observations → Data Quality Engine → Cross-Source Reconciliation/Consensus → Canonical Market/Data State → BLACKDARK Intelligence / Decision Truth`

Names may reuse existing repository owners, but the functional responsibility may not be omitted or replaced by blind last-write-wins behavior.

## RESTORE-006 — Economic revision/vintage truth
For economic, regulatory, macro or any revisable dataset, retain **revision/vintage / as-known-at** information where available and material. Historical replay/backtesting must use what was knowable at the decision timestamp, not silently substitute later revised values.

## RESTORE-007 — Free-first operating rule
Free/open/direct sources are preferred where they satisfy measured requirements. “Free” alone is not a defect. The actual risks are:
- single-source dependency
- absent contractual SLA where one is needed
- inadequate quota
- inadequate historical depth
- unclear licensing/redistribution/storage rights
- unmeasured reliability
- insufficient decision-grade depth/latency/quality

A paid provider is introduced only when a measured material product gap justifies it. In no-money mode, capability truthfulness wins over fabricated equivalence.

## RESTORE-008 — Source-role discipline
Direct official venue feeds SHOULD be evaluated first for venue-specific real-time truth. Aggregators SHOULD normally serve breadth/discovery/metadata/reference/cross-check/history unless separately proven suitable for execution-sensitive use. No aggregator is automatically execution-grade.

## RESTORE-009 — User-facing strategic target
The end-state is not another crypto price site. The data architecture must serve retail, professional, B2B, funds and acquisition-grade diligence by producing auditable evidence-backed intelligence, including Live Decision Pulse / Decision Truth surfaces, rather than maximizing connector count.

## RESTORE-010 — Mandatory execution sequencing gate
Cursor MUST implement the system in ordered atomic units. It MUST NOT start Phase II merely because adapters exist. Phase I must first prove:
- canonical ownership
- source admission
- normalization
- quality/freshness gates
- reconciliation/conflict behavior
- provenance/lineage
- historical/replay controls
- observability
- fallback/degrade/abstain
- tests and evidence

Only then may source breadth expand.

## RESTORE-011 — Closure reconciliation
Before `PASS_ENGINEERING_DATA=true`, Cursor MUST explicitly reconcile **RESTORE-001→RESTORE-010** in addition to DATA-001→DATA-100 and report:

```text
RESTORED_PRIOR_DECISIONS_ACCOUNTED_FOR=100%
RESTORED_PRIOR_DECISIONS_MISSED=[]
PHASE_I_SOURCE_SCOPE_DEFINED=true
PREMATURE_100_SOURCE_EXPANSION=false
DATA_TRUST_OBSERVATION_CONTRACT_PASS=true
CROSS_SOURCE_RECONCILIATION_PASS=true
CANONICAL_MARKET_DATA_STATE_PASS=true
SOURCE_CONFLICT_POLICY_PASS=true
REVISION_VINTAGE_AS_KNOWN_AT_PASS=true
```

If any of these cannot be proven locally, `PASS_ENGINEERING_DATA=true` MUST remain false.
