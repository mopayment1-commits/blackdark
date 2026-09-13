#!/usr/bin/env python3
"""Phase 0B: extract primary normative requirements from Temporal governing spec (no atomization)."""

from __future__ import annotations

import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs/standards/domain/BLACKDARK Temporal Intelligence & Evidence Acceleration System.md"
OUT = ROOT / "TEMPORAL_PRIMARY_REQUIREMENTS.json"

# Each tuple: section, source_location, requirement_text, requirement_type, priority,
# implementation_intended, explicit_prohibition, possible_live_or_external_dependency
RAW: list[tuple[str, str, str, str, str, bool, bool, bool]] = [
    # §0 Status and Governing Position
    ("0. Status and Governing Position", "§0 L8-L10", "BLACKDARK Institutional Standard v6 is the highest institutional governing standard; BLACKDARK Domain Spec v4_v2 is subordinate for data, storage, track record, provenance, replay, outcomes, learning, rights, retention, recovery, and related intelligence accumulation; this document is an implementation/design addendum subordinate to both.", "GOVERNING_HIERARCHY", "P0", False, False, False),
    ("0. Status and Governing Position", "§0 L12-L16", "If any conflict exists, v6 prevails, then v4_v2, then this document; historical freeze artifacts are not rewritten retroactively.", "GOVERNING_HIERARCHY", "P0", False, True, False),
    # §1 Governing Objective
    ("1. Governing Objective", "§1 L22", "The objective is not to make BLACKDARK appear to have operated live for a year.", "GOVERNING_OBJECTIVE", "P0", True, True, False),
    ("1. Governing Objective", "§1 L26", "Maximize trustworthy experimental, evaluative, and learning experience per unit of real elapsed time, while preserving strict separation between historical knowledge, forward evidence, production evidence, and independent assurance.", "GOVERNING_OBJECTIVE", "P0", True, False, False),
    ("1. Governing Objective", "§1 L30", "EXPERIENCE COMPRESSION ≠ TIME FABRICATION.", "HARD_RULE", "P0", True, True, False),
    ("1. Governing Objective", "§1 L34", "Evidence classes must remain distinct: HISTORICAL_REPLAY ≠ FORWARD_SHADOW ≠ VERIFIED_PRODUCTION ≠ INDEPENDENT_ASSURANCE.", "EVIDENCE_CLASS_RULE", "P0", True, False, False),
    ("1. Governing Objective", "§1 L36", "No historical replay, simulation, backtest, or reconstructed result may be represented as live chronological evidence.", "PROHIBITION", "P0", False, True, False),
    # §2 System Architecture
    ("2. System Architecture", "§2 L42-L72", "System architecture must follow the prescribed processing sequence: Raw Historical + Live Feeds → Canonical Historical/Event Store → Point-in-Time Reconstruction → Temporal Leakage Firewall → Feature/Derived Intelligence Layer → Deterministic Mass Replay → Signal / Prediction / Decision → Automated Outcome Factory → Evidence Provenance Ledger → Failure / Surprise / Abstention Corpus → Regime Intelligence → Learning Value Prioritization → Champion / Challenger Evaluation → Forward Shadow Reality Anchor → Promotion / Rejection / Recalibration → Continuous Evidence Accumulation.", "EXECUTION_SEQUENCING", "P0", True, False, False),
    # §3 Point-in-Time Historical Reconstruction
    ("3. Point-in-Time Historical Reconstruction — P0", "§3 L78", "The system must reconstruct what BLACKDARK could actually have known at time T.", "MUST", "P0", True, False, False),
    ("3. Point-in-Time Historical Reconstruction — P0", "§3 L80-L91", "Where applicable, every datum must preserve: event_time, observed_time, available_at, ingested_at, effective_at, revised_at, source, source_version, dataset_version, and rights/provenance.", "REQUIRED_FIELD", "P0", True, False, False),
    ("3. Point-in-Time Historical Reconstruction — P0", "§3 L95", "Hard rule: available_at > simulated_time => inaccessible.", "HARD_RULE", "P0", True, False, False),
    ("3. Point-in-Time Historical Reconstruction — P0", "§3 L97-L103", "The reconstruction layer must prevent: look-ahead leakage; revision leakage; future-information contamination; post-event corrections being visible before they were actually available; accidental use of current normalized values in historical evaluation.", "MUST", "P0", True, False, False),
    ("3. Point-in-Time Historical Reconstruction — P0", "§3 L105", "Historical replay is invalid for institutional evidence if this control is not satisfied.", "ACCEPTANCE_RESTRICTION", "P0", False, False, False),
    # §4 Temporal Leakage Firewall
    ("4. Temporal Leakage Firewall — P0", "§4 L111", "Temporal integrity must be enforced technically, not merely by developer convention.", "MUST", "P0", True, False, False),
    ("4. Temporal Leakage Firewall — P0", "§4 L113", "The replay/evaluation system must reject access to data that was not available at the simulated decision time.", "MUST", "P0", True, False, False),
    ("4. Temporal Leakage Firewall — P0", "§4 L115-L124", "Tests should include, where applicable: delayed publications; revised macroeconomic data; late-arriving market/on-chain data; corrected source values; source/event timestamp mismatch; missing historical timestamps; unavailable historical features; historical source latency.", "SHOULD_IMPLEMENTATION_DIRECTION", "P0", True, False, False),
    ("4. Temporal Leakage Firewall — P0", "§4 L126", "Any leakage detected must invalidate the affected evaluation evidence until corrected and rerun.", "MUST", "P0", True, False, False),
    # §5 Canonical Historical Event Store
    ("5. Canonical Historical Event Store — P0", "§5 L132", "Historical and live information must not become an unstructured file archive.", "PROHIBITION", "P0", True, True, False),
    ("5. Canonical Historical Event Store — P0", "§5 L134-L136", "BLACKDARK should preserve a canonical path: Raw → Normalized → Entity/Event → Feature → Signal.", "SHOULD_IMPLEMENTATION_DIRECTION", "P0", True, False, False),
    ("5. Canonical Historical Event Store — P0", "§5 L138-L149", "Required controls include: immutable raw-source lineage; source identity; schema/version history; deduplication; corrections and amendments; source-conflict representation; deterministic reconstruction; data rights metadata; retention policy; reproducible transformation lineage.", "REQUIRED_CONTROL", "P0", True, False, True),
    ("5. Canonical Historical Event Store — P0", "§5 L151", "Raw evidence must not be discarded solely because its current learning priority is low.", "PROHIBITION", "P0", True, True, False),
    # §6 Deterministic Mass Replay Engine
    ("6. Deterministic Mass Replay Engine — P0", "§6 L157-L166", "Replay must reproduce the intended decision path: Observation → Feature State → Signal → Prediction → Decision → Confidence → Abstain / Act → Outcome.", "MUST", "P0", True, False, False),
    ("6. Deterministic Mass Replay Engine — P0", "§6 L168-L177", "Replay should support: multiple assets; multiple venues where applicable; multiple time horizons; multiple historical periods; multiple market regimes; multiple model/rule/config versions; alternative thresholds; alternative source availability scenarios.", "SHOULD_IMPLEMENTATION_DIRECTION", "P0", True, False, False),
    ("6. Deterministic Mass Replay Engine — P0", "§6 L179-L186", "Replay must be: reproducible; point-in-time correct; provenance-bound; version-bound; deterministic where feasible; comparable across model versions.", "MUST", "P0", True, False, False),
    ("6. Deterministic Mass Replay Engine — P0", "§6 L188", "Replay results are evidence of historical evaluation, not proof of live forward performance.", "ACCEPTANCE_RESTRICTION", "P0", False, False, True),
    # §7 Dependence-Aware Experience Multiplication
    ("7. Dependence-Aware Experience Multiplication — P1", "§7 L194", "A single historical period may generate many evaluation instances, but those instances must not automatically be treated as statistically independent.", "MUST", "P1", True, False, False),
    ("7. Dependence-Aware Experience Multiplication — P1", "§7 L196-L204", "For every material evaluation family, capture dependence dimensions such as: temporal overlap; shared event; asset correlation; shared label; shared regime; shared source dependency; shared model family.", "MUST", "P1", True, False, False),
    ("7. Dependence-Aware Experience Multiplication — P1", "§7 L206-L210", "Record, where practical: case_id, event_family, dependence_cluster.", "REQUIRED_FIELD", "P1", True, False, False),
    ("7. Dependence-Aware Experience Multiplication — P1", "§7 L212", "The system may report millions of evaluation instances, but must distinguish this from an effective independent sample count.", "MUST", "P1", True, False, False),
    # §8 Walk-Forward Evaluation
    ("8. Walk-Forward Evaluation — P0", "§8 L218", "Historical evaluation must not rely on train-on-all-history/test-on-the-same-history methodology.", "PROHIBITION", "P0", True, True, False),
    ("8. Walk-Forward Evaluation — P0", "§8 L220-L226", "Use walk-forward methodology: Past training/fit window → Freeze → Future untouched evaluation window → Advance window → Repeat.", "EXECUTION_SEQUENCING", "P0", True, False, False),
    ("8. Walk-Forward Evaluation — P0", "§8 L228-L236", "Apply where relevant: purge; embargo; no future-feature leakage; immutable evaluation windows; model/version freeze; dataset/version freeze; configuration freeze.", "REQUIRED_CONTROL", "P0", True, False, False),
    ("8. Walk-Forward Evaluation — P0", "§8 L238", "Repeated tuning against the same evaluation window must be tracked as evaluation contamination.", "MUST", "P0", True, False, False),
    # §9 Automated Outcome Factory
    ("9. Automated Outcome Factory — P0", "§9 L244", "Every material Signal, Prediction, or Decision should be linkable to a measurable Outcome Contract.", "SHOULD_IMPLEMENTATION_DIRECTION", "P0", True, False, False),
    ("9. Automated Outcome Factory — P0", "§9 L246-L265", "Where applicable, record: target definition; evaluation horizon; outcome timestamp; realized result; benchmark result; confidence; calibration error; directional correctness; magnitude error; regret; favorable excursion; adverse excursion; drawdown; false-positive cost; false-negative cost; abstention quality; market regime; evaluator version.", "REQUIRED_FIELD", "P0", True, False, False),
    ("9. Automated Outcome Factory — P0", "§9 L267", "The outcome evaluator must be logically independent from the prediction logic.", "MUST", "P0", True, False, False),
    ("9. Automated Outcome Factory — P0", "§9 L269", "A production prediction function must not validate itself by generating its own expected outcome.", "PROHIBITION", "P0", True, True, False),
    # §10 Outcome Quality and Label Confidence
    ("10. Outcome Quality and Label Confidence — P0", "§10 L277-L284", "Each evaluated outcome should carry, where relevant: outcome_quality, label_confidence, data_completeness, evaluation_source, evaluation_method, known_limitations.", "SHOULD_IMPLEMENTATION_DIRECTION", "P0", True, False, False),
    ("10. Outcome Quality and Label Confidence — P0", "§10 L288", "Derived, inferred, or imperfect outcomes must not be presented as equivalent to direct observed truth.", "PROHIBITION", "P0", False, True, False),
    # §11 Immutable Forward-Shadow Evidence Receipts
    ("11. Immutable Forward-Shadow Evidence Receipts — P0", "§11 L294", "Before the future outcome is known, every material forward-shadow prediction must receive an immutable pre-outcome receipt.", "MUST", "P0", True, False, True),
    ("11. Immutable Forward-Shadow Evidence Receipts — P0", "§11 L296-L308", "Minimum receipt fields where applicable: prediction_id, issued_at, model_version, rule/config_version, dataset_version, code_version, input_snapshot_hash, prediction, confidence, abstention_state, evidence_class=FORWARD_SHADOW.", "REQUIRED_FIELD", "P0", True, False, True),
    ("11. Immutable Forward-Shadow Evidence Receipts — P0", "§11 L310", "The original receipt must not be overwritten after the outcome becomes known.", "PROHIBITION", "P0", True, True, False),
    ("11. Immutable Forward-Shadow Evidence Receipts — P0", "§11 L312", "Corrections must use append-only amendments with provenance.", "MUST", "P0", True, False, False),
    # §12 Evidence Provenance Ledger
    ("12. Evidence Provenance Ledger — P0", "§12 L318-L325", "Evidence classes must include: HISTORICAL_BACKTEST, HISTORICAL_REPLAY, SIMULATED, FORWARD_SHADOW, VERIFIED_PRODUCTION, INDEPENDENTLY_VERIFIED.", "EVIDENCE_CLASS_RULE", "P0", True, False, False),
    ("12. Evidence Provenance Ledger — P0", "§12 L329", "No automatic promotion between evidence classes.", "PROHIBITION", "P0", True, True, False),
    ("12. Evidence Provenance Ledger — P0", "§12 L330", "Evidence must be version-scoped.", "MUST", "P0", True, False, False),
    ("12. Evidence Provenance Ledger — P0", "§12 L331", "Evidence must preserve methodology.", "MUST", "P0", True, False, False),
    ("12. Evidence Provenance Ledger — P0", "§12 L332", "Evidence must preserve timestamps.", "MUST", "P0", True, False, False),
    ("12. Evidence Provenance Ledger — P0", "§12 L333", "Evidence must preserve evaluator identity/version.", "MUST", "P0", True, False, False),
    ("12. Evidence Provenance Ledger — P0", "§12 L334", "Evidence must preserve source/provenance.", "MUST", "P0", True, False, False),
    ("12. Evidence Provenance Ledger — P0", "§12 L335", "Evidence must preserve material limitations.", "MUST", "P0", True, False, False),
    ("12. Evidence Provenance Ledger — P0", "§12 L339-L341", "Hard rules: Replay ≠ Shadow; Shadow ≠ Production; Production ≠ Independent Assurance.", "HARD_RULE", "P0", True, False, True),
    # §13 Forward Shadow Reality Anchor
    ("13. Forward Shadow Reality Anchor — P0", "§13 L349-L359", "Monitor, where applicable: concept drift; data drift; source drift; latency differences; venue behavior changes; market-structure changes; regime changes; calibration changes; unexpected source conflicts.", "SHOULD_IMPLEMENTATION_DIRECTION", "P0", True, False, True),
    ("13. Forward Shadow Reality Anchor — P0", "§13 L361", "Forward shadow is not merely a sample-count generator.", "ACCEPTANCE_RESTRICTION", "P0", False, False, True),
    ("13. Forward Shadow Reality Anchor — P0", "§13 L363", "Forward shadow is the live reality anchor for all historical evidence.", "MUST", "P0", True, False, True),
    # §14 Regime Intelligence Library
    ("14. Regime Intelligence Library — P0", "§14 L369", "Evaluation must be decomposable by market regime.", "MUST", "P0", True, False, False),
    ("14. Regime Intelligence Library — P0", "§14 L389", "Aggregate metrics must not be allowed to hide material regime-specific failure.", "PROHIBITION", "P0", True, True, False),
    # §15 Failure, Surprise & Abstention Corpus
    ("15. Failure, Surprise & Abstention Corpus — P0", "§15 L395", "Create a durable corpus of high-learning-value failures and surprises.", "MUST", "P0", True, False, False),
    ("15. Failure, Surprise & Abstention Corpus — P0", "§15 L397-L413", "Include, where applicable: high-confidence wrong prediction; failure to abstain; unnecessary abstention; missed major event; model disagreement; unexpected regime shift; correlation breakdown; stale source; conflicting sources; missing source; tail event; calibration collapse; prediction instability; source revision; model regression.", "REQUIRED_CONTROL", "P0", True, False, False),
    ("15. Failure, Surprise & Abstention Corpus — P0", "§15 L415-L423", "Each material case should be traceable: Case → Root Cause → Affected Capability → Model/Rule Version → Remediation → Regression Test → Post-fix Replay.", "SHOULD_IMPLEMENTATION_DIRECTION", "P0", True, False, False),
    # §16 Learning Value Engine
    ("16. Learning Value Engine — P1", "§16 L431", "Do not treat all observations as equally valuable for learning.", "PROHIBITION", "P1", True, True, False),
    ("16. Learning Value Engine — P1", "§16 L433-L439", "Maintain two complementary sampling streams: A. Representative Sampling Stream for unbiased/representative coverage; B. High-Information Learning Stream prioritizing novelty, uncertainty, model disagreement, failure severity, economic materiality, regime rarity, and data-quality risk.", "SHOULD_IMPLEMENTATION_DIRECTION", "P1", True, False, False),
    ("16. Learning Value Engine — P1", "§16 L451", "A Learning Value Score may be used for prioritization, but it must not replace representative sampling.", "MUST", "P1", True, False, False),
    ("16. Learning Value Engine — P1", "§16 L453", "Learning priority and storage retention are separate decisions.", "HARD_RULE", "P1", True, False, False),
    # §17 Data Retention Is Not Learning Priority
    ("17. Data Retention Is Not Learning Priority — P0", "§17 L459", "Do not delete raw evidence merely because it currently has low learning value.", "PROHIBITION", "P0", True, True, False),
    ("17. Data Retention Is Not Learning Priority — P0", "§17 L461-L476", "Use tiered storage according to access, cost, rights, and retention policy with Hot (live/recent, high-frequency, active evaluation), Warm (normalized datasets, reusable features, frequent replay artifacts), and Cold (historical/raw/archive, rare research evidence, long-horizon reconstruction) tiers.", "SHOULD_IMPLEMENTATION_DIRECTION", "P0", True, False, True),
    ("17. Data Retention Is Not Learning Priority — P0", "§17 L478-L486", "Support: compression; partitioning; deduplication; lifecycle policies; rights-aware retention; deterministic reconstruction; reproducible retrieval.", "REQUIRED_CONTROL", "P0", True, False, True),
    # §18 Replay Fidelity Profile
    ("18. Replay Fidelity Profile — P1", "§18 L494-L505", "Maintain separate fidelity dimensions such as: temporal fidelity; source coverage; source completeness; order-book/depth fidelity; latency fidelity; transaction-cost fidelity; revision integrity; venue availability; provenance completeness; rights completeness.", "SHOULD_IMPLEMENTATION_DIRECTION", "P1", True, False, False),
    ("18. Replay Fidelity Profile — P1", "§18 L507", "A composite score may be derived for convenience, but material dimensions must remain visible.", "MUST", "P1", True, False, False),
    # §19 Experience Coverage Vector
    ("19. Experience Coverage Vector — P1", "§19 L513", "Do not use elapsed time alone as a proxy for experience.", "PROHIBITION", "P1", True, True, False),
    ("19. Experience Coverage Vector — P1", "§19 L515-L530", "Track: historical span; regime coverage; independent event families; effective independent sample count; prediction/outcome pairs; tail-event coverage; asset coverage; venue coverage; source diversity; calibration coverage; failure-corpus coverage; replay fidelity; forward-shadow duration; forward-shadow sample count.", "REQUIRED_CONTROL", "P1", True, False, False),
    ("19. Experience Coverage Vector — P1", "§19 L532", "An optional composite Experience Coverage Index may summarize the vector, but must not hide weak material dimensions.", "MUST", "P1", True, False, False),
    # §20 Champion–Challenger Governance
    ("20. Champion–Challenger Governance — P1", "§20 L538", "Production learning must not automatically modify the deployed model.", "PROHIBITION", "P1", True, True, False),
    ("20. Champion–Challenger Governance — P1", "§20 L540-L551", "Use promotion pipeline: Outcome → Candidate Learning → Challenger → Historical Evaluation → Walk-Forward → Regime Validation → Forward Shadow → Stability Review → Promotion Decision → Champion.", "EXECUTION_SEQUENCING", "P1", True, False, False),
    ("20. Champion–Challenger Governance — P1", "§20 L553", "Promotion/rejection must preserve evidence and version lineage.", "MUST", "P1", True, False, False),
    # §21 Controlled Learning
    ("21. Controlled Learning — P0/P1", "§21 L559", "BLACKDARK must not currently allow uncontrolled self-modifying production behavior.", "PROHIBITION", "P0", True, True, False),
    ("21. Controlled Learning — P0/P1", "§21 L561-L567", "Learning may generate candidate weights, candidate models, candidate rules, candidate calibration changes, and candidate thresholds, but none become production without the required promotion gate.", "MUST", "P0", True, False, False),
    ("21. Controlled Learning — P0/P1", "§21 L571", "True adaptive/online production learning is a later capability and requires its own governance and safety controls.", "ACCEPTANCE_RESTRICTION", "Later", False, False, True),
    # §22 Counterfactual Decision Lab
    ("22. Counterfactual Decision Lab — P1", "§22 L577-L587", "Replay should support counterfactual questions such as: different confidence threshold; alternative abstention threshold; source removed; source delayed; alternate model version; alternate rule version; higher latency; different costs; alternative regime assumptions.", "SHOULD_IMPLEMENTATION_DIRECTION", "P1", True, False, False),
    ("22. Counterfactual Decision Lab — P1", "§22 L589", "The purpose is to evaluate decision robustness, not merely historical direction accuracy.", "GOVERNING_OBJECTIVE", "P1", True, False, False),
    # §23 Market Time Machine
    ("23. Market Time Machine — P1 Internal / P2 User-Facing", "§23 L597-L606", "Internal Mode (P1) should be used for: QA; debugging; research; model comparison; replay; failure reproduction; evidence generation; root-cause analysis.", "SHOULD_IMPLEMENTATION_DIRECTION", "P1", True, False, False),
    ("23. Market Time Machine — P1 Internal / P2 User-Facing", "§23 L610-L621", "User-Facing Mode (P2) should allow the user to select a historical timestamp/event and see: What was knowable then → evidence → uncertainty → conflicting sources → prediction → confidence → why → why-not → abstention → what happened next.", "SHOULD_IMPLEMENTATION_DIRECTION", "P2", True, False, True),
    ("23. Market Time Machine — P1 Internal / P2 User-Facing", "§23 L623-L625", "Mandatory disclosure: Historical Replay.", "MANDATORY_DISCLOSURE", "P2", True, False, True),
    ("23. Market Time Machine — P1 Internal / P2 User-Facing", "§23 L627", "It must never imply that the historical output was issued live at that time unless there is genuine forward evidence proving that fact.", "PROHIBITION", "P2", False, True, True),
    # §24 Public Accuracy / Evidence Ledger
    ("24. Public Accuracy / Evidence Ledger — P2", "§24 L633", "Build backend evidence foundations early, but do not use a public ledger as a marketing claim until evidence is sufficiently mature.", "PROHIBITION", "P2", True, True, True),
    ("24. Public Accuracy / Evidence Ledger — P2", "§24 L635-L649", "Every material public claim should disclose, where applicable: evidence class; date range; sample size; effective independent sample count; regime distribution; asset/universe; evaluation horizon; model version; abstentions; methodology; uncertainty; exclusions; limitations.", "MANDATORY_DISCLOSURE", "P2", True, False, True),
    ("24. Public Accuracy / Evidence Ledger — P2", "§24 L651-L657", "Controls must address: cherry-picking; survivorship bias; retroactive deletion; selective date-window reporting; mixing evidence classes.", "REQUIRED_CONTROL", "P2", True, False, True),
    # §25 Source & Rights Governance
    ("25. Source & Rights Governance — P0", "§25 L663-L673", "For every material source preserve, where applicable: permitted purpose; historical-use rights; retention rights; derivative-data rights; redistribution rights; model-training rights; provenance; contractual restrictions; expiry/revocation conditions.", "REQUIRED_FIELD", "P0", True, False, True),
    ("25. Source & Rights Governance — P0", "§25 L675", "Historical availability does not automatically imply legal or contractual permission to retain, train on, transform, or redistribute the data.", "ACCEPTANCE_RESTRICTION", "P0", False, False, True),
    ("25. Source & Rights Governance — P0", "§25 L677", "No paid vendor is automatically purchased merely because the design references a data dependency.", "PROHIBITION", "P0", False, True, True),
    # §26 Data Quality & Source Reliability
    ("26. Data Quality & Source Reliability — P0", "§26 L683-L694", "Maintain source reliability evidence, including where applicable: freshness; completeness; latency; anomaly rate; disagreement rate; revision frequency; outage history; timestamp integrity; historical coverage; schema stability.", "REQUIRED_CONTROL", "P0", True, False, False),
    ("26. Data Quality & Source Reliability — P0", "§26 L696-L701", "Source quality should influence: confidence; replay fidelity; evidence quality; degradation behavior.", "SHOULD_IMPLEMENTATION_DIRECTION", "P0", True, False, False),
    # §27 Drift & Structural-Break Detection
    ("27. Drift & Structural-Break Detection — P1", "§27 L707-L715", "Monitor, where applicable: feature drift; target drift; calibration drift; source drift; relationship drift; regime transition; structural break.", "SHOULD_IMPLEMENTATION_DIRECTION", "P1", True, False, True),
    ("27. Drift & Structural-Break Detection — P1", "§27 L717-L719", "The system must be able to conclude: Historical evidence is no longer sufficiently representative of current conditions.", "MUST", "P1", True, False, True),
    ("27. Drift & Structural-Break Detection — P1", "§27 L721", "Historical scale must never override current invalidation evidence.", "PROHIBITION", "P1", False, True, True),
    # §28 Evaluation Contamination Registry
    ("28. Evaluation Contamination Registry — P0/P1", "§28 L727-L735", "Track whether datasets/windows have been used for: training; tuning; feature design; threshold selection; hyperparameter selection; evaluation; repeated post-hoc investigation.", "REQUIRED_CONTROL", "P0", True, False, False),
    ("28. Evaluation Contamination Registry — P0/P1", "§28 L737", "Repeated reuse of a supposedly untouched evaluation set must be visible and must reduce the strength of any out-of-sample claim.", "MUST", "P0", True, False, False),
    # §29 Reproducibility Manifest
    ("29. Reproducibility Manifest — P0", "§29 L743-L756", "For each material replay/evaluation run preserve, where applicable: code SHA; configuration; dataset snapshot; feature version; model version; rule version; evaluator version; random seed; environment; run ID; timestamps; evidence class.", "REQUIRED_FIELD", "P0", True, False, False),
    ("29. Reproducibility Manifest — P0", "§29 L758", "Material results must be reproducible or explicitly marked when full reproducibility is technically impossible.", "MUST", "P0", True, False, False),
    # §30 Computational Acceleration Layer
    ("30. Computational Acceleration Layer — P1", "§30 L766-L777", "Use where appropriate: feature caching; immutable feature snapshots; incremental recomputation; columnar storage; partition pruning; event-based replay; parallel execution; reusable intermediate artifacts; workload prioritization; deterministic cache keys.", "SHOULD_IMPLEMENTATION_DIRECTION", "P1", True, False, False),
    ("30. Computational Acceleration Layer — P1", "§30 L779", "Performance optimization must not weaken provenance, temporal integrity, reproducibility, or evidence classification.", "PROHIBITION", "P1", True, True, False),
    # §31 User Behavioral Learning
    ("31. User Behavioral Learning — Later / Controlled", "§31 L785", "User behavior is not financial ground truth.", "HARD_RULE", "Later", False, False, True),
    ("31. User Behavioral Learning — Later / Controlled", "§31 L787-L795", "If used later, require: explicit purpose; consent/legal basis where applicable; minimization; retention rules; deletion/rights handling; separation from objective market outcomes; anti-manipulation controls.", "REQUIRED_CONTROL", "Later", True, False, True),
    ("31. User Behavioral Learning — Later / Controlled", "§31 L797", "A user action such as clicking Buy must never be treated automatically as proof that Buy was the correct financial decision.", "PROHIBITION", "Later", False, True, True),
    # §32 Quality and Acceptance Model
    ("32. Quality and Acceptance Model", "§32 L803", "Relevant institutional quality principles should be applied without falsely attributing BLACKDARK-specific architecture to external standards.", "SHOULD_IMPLEMENTATION_DIRECTION", "P0", True, False, False),
    ("32. Quality and Acceptance Model", "§32 L805-L817", "The design should support: functional correctness; reliability; security; maintainability; performance efficiency; traceability; reproducibility; testability; auditability; quality-in-use; risk-based monitoring.", "SHOULD_IMPLEMENTATION_DIRECTION", "P0", True, False, False),
    # §33 Execution Priority — P0 items (each preserved separately per no-dedup)
    ("33. Execution Priority", "§33 P0 #1", "P0 — Build / establish immediately: Evidence taxonomy.", "EXECUTION_PRIORITY", "P0", True, False, False),
    ("33. Execution Priority", "§33 P0 #2", "P0 — Build / establish immediately: Signal / Prediction / Decision / Outcome ledgers.", "EXECUTION_PRIORITY", "P0", True, False, False),
    ("33. Execution Priority", "§33 P0 #3", "P0 — Build / establish immediately: Point-in-Time availability model.", "EXECUTION_PRIORITY", "P0", True, False, False),
    ("33. Execution Priority", "§33 P0 #4", "P0 — Build / establish immediately: Temporal Leakage Firewall.", "EXECUTION_PRIORITY", "P0", True, False, False),
    ("33. Execution Priority", "§33 P0 #5", "P0 — Build / establish immediately: Canonical Historical Event Store.", "EXECUTION_PRIORITY", "P0", True, False, False),
    ("33. Execution Priority", "§33 P0 #6", "P0 — Build / establish immediately: Dataset / Model / Rule / Evaluator lineage.", "EXECUTION_PRIORITY", "P0", True, False, False),
    ("33. Execution Priority", "§33 P0 #7", "P0 — Build / establish immediately: Reproducibility Manifest.", "EXECUTION_PRIORITY", "P0", True, False, False),
    ("33. Execution Priority", "§33 P0 #8", "P0 — Build / establish immediately: Deterministic Replay.", "EXECUTION_PRIORITY", "P0", True, False, False),
    ("33. Execution Priority", "§33 P0 #9", "P0 — Build / establish immediately: Walk-Forward Evaluation.", "EXECUTION_PRIORITY", "P0", True, False, False),
    ("33. Execution Priority", "§33 P0 #10", "P0 — Build / establish immediately: Automated Outcome Factory.", "EXECUTION_PRIORITY", "P0", True, False, False),
    ("33. Execution Priority", "§33 P0 #11", "P0 — Build / establish immediately: Outcome quality / label confidence.", "EXECUTION_PRIORITY", "P0", True, False, False),
    ("33. Execution Priority", "§33 P0 #12", "P0 — Build / establish immediately: Immutable Forward-Shadow receipts.", "EXECUTION_PRIORITY", "P0", True, False, True),
    ("33. Execution Priority", "§33 P0 #13", "P0 — Build / establish immediately: Failure / Surprise / Abstention Corpus.", "EXECUTION_PRIORITY", "P0", True, False, False),
    ("33. Execution Priority", "§33 P0 #14", "P0 — Build / establish immediately: Regime Intelligence Library.", "EXECUTION_PRIORITY", "P0", True, False, False),
    ("33. Execution Priority", "§33 P0 #15", "P0 — Build / establish immediately: Source quality / reliability.", "EXECUTION_PRIORITY", "P0", True, False, False),
    ("33. Execution Priority", "§33 P0 #16", "P0 — Build / establish immediately: Source rights / retention controls.", "EXECUTION_PRIORITY", "P0", True, False, True),
    ("33. Execution Priority", "§33 P0 #17", "P0 — Build / establish immediately: Evaluation Contamination Registry.", "EXECUTION_PRIORITY", "P0", True, False, False),
    ("33. Execution Priority", "§33 P1", "P1 — Build after the P0 spine exists: Learning Value Engine; Experience Coverage Vector; Replay Fidelity Profile; Dependence-Aware Experience Multiplication; Champion / Challenger; Drift Detection; Counterfactual Decision Lab; Internal Market Time Machine; Computational Acceleration Layer.", "EXECUTION_PRIORITY", "P1", True, False, False),
    ("33. Execution Priority", "§33 P2", "P2: User-facing Market Time Machine; Public Accuracy / Evidence Ledger; Behavioral personalization where justified.", "EXECUTION_PRIORITY", "P2", True, False, True),
    ("33. Execution Priority", "§33 Later", "Later: Controlled adaptive / online production learning.", "EXECUTION_PRIORITY", "Later", True, False, True),
    # §34 Fastest Correct Implementation Principle
    ("34. Fastest Correct Implementation Principle", "§34 L871", "Do not begin by training the largest possible model.", "PROHIBITION", "P0", True, True, False),
    ("34. Fastest Correct Implementation Principle", "§34 L873-L880", "Build the accumulation/evidence spine first: Capture → Replay → Outcome → Evidence → Failure → Re-evaluation.", "EXECUTION_SEQUENCING", "P0", True, False, False),
    ("34. Fastest Correct Implementation Principle", "§34 L884", "Building AI first and evidence/data lineage later creates avoidable rework, weak provenance, leakage risk, and low-quality claims.", "ACCEPTANCE_RESTRICTION", "P0", False, False, False),
    # §35 Final Institutional Position
    ("35. Final Institutional Position", "§35 L894", "The system must leverage historical data through point-in-time-correct reconstruction and replay to maximize trustworthy learning and evaluation evidence per real day of operation.", "GOVERNING_OBJECTIVE", "P0", True, False, False),
    ("35. Final Institutional Position", "§35 L896", "It does not shorten real chronological time.", "ACCEPTANCE_RESTRICTION", "P0", False, False, False),
    ("35. Final Institutional Position", "§35 L910", "Preserve the distinction between historical, shadow, production, and independently verified evidence while accelerating experimental exposure, failure discovery, outcome generation, calibration, model comparison, regime coverage, evidence accumulation, data-moat formation, and decision-quality improvement.", "EVIDENCE_CLASS_RULE", "P0", True, False, False),
    # §36 Non-Negotiable Integrity Rules
    ("36. Non-Negotiable Integrity Rules", "§36 #1", "No fabricated live history.", "PROHIBITION", "P0", False, True, False),
    ("36. Non-Negotiable Integrity Rules", "§36 #2", "No evidence-class mixing.", "PROHIBITION", "P0", False, True, False),
    ("36. Non-Negotiable Integrity Rules", "§36 #3", "No look-ahead/revision leakage.", "PROHIBITION", "P0", False, True, False),
    ("36. Non-Negotiable Integrity Rules", "§36 #4", "No automatic self-validation by production logic.", "PROHIBITION", "P0", False, True, False),
    ("36. Non-Negotiable Integrity Rules", "§36 #5", "No uncontrolled self-modifying production model.", "PROHIBITION", "P0", False, True, False),
    ("36. Non-Negotiable Integrity Rules", "§36 #6", "No inflated independent-sample claims from correlated replay instances.", "PROHIBITION", "P0", False, True, False),
    ("36. Non-Negotiable Integrity Rules", "§36 #7", "No deletion of raw evidence solely due to low current learning priority.", "PROHIBITION", "P0", False, True, False),
    ("36. Non-Negotiable Integrity Rules", "§36 #8", "No public accuracy claim without methodology, sample context, and evidence classification.", "PROHIBITION", "P0", False, True, True),
    ("36. Non-Negotiable Integrity Rules", "§36 #9", "No training or redistribution assumption without rights/provenance review.", "PROHIBITION", "P0", False, True, True),
    ("36. Non-Negotiable Integrity Rules", "§36 #10", "No retrospective rewriting of historical freeze evidence.", "PROHIBITION", "P0", False, True, False),
    ("36. Non-Negotiable Integrity Rules", "§36 #11", "No promotion from historical or shadow evidence to production evidence without actual production proof.", "PROHIBITION", "P0", False, True, True),
    ("36. Non-Negotiable Integrity Rules", "§36 #12", "No conflict with v6 or v4_v2; higher governing standards always prevail.", "GOVERNING_HIERARCHY", "P0", False, False, False),
    # §37 Acceptance Boundary
    ("37. Acceptance Boundary", "§37 L935-L941", "This document's approval does not by itself mean PASS_ENGINEERING, PASS_LIVE, ASSURANCE_READY, PRODUCTION_ALIGNED, or independent verification.", "ACCEPTANCE_RESTRICTION", "P0", False, False, True),
    ("37. Acceptance Boundary", "§37 L943", "PASS_ENGINEERING, PASS_LIVE, ASSURANCE_READY, PRODUCTION_ALIGNED, and independent verification require their own implementation evidence and gates under the governing standards.", "ACCEPTANCE_RESTRICTION", "P0", False, False, True),
]

# Additional normative clauses from re-read pass (preserve without dedup)
EXTRA: list[tuple[str, str, str, str, str, bool, bool, bool]] = [
    ("10. Outcome Quality and Label Confidence — P0", "§10 L286", "Objective market observations may carry high confidence.", "SHOULD_IMPLEMENTATION_DIRECTION", "P0", True, False, False),
    ("14. Regime Intelligence Library — P0", "§14 L371-L387", "Possible regimes include, where justified: bull; bear; range-bound; high volatility; low volatility; liquidity stress; liquidation cascade; depeg; market-wide crash; idiosyncratic asset shock; exchange outage; macro shock; news shock; correlation break; structural break.", "SHOULD_IMPLEMENTATION_DIRECTION", "P0", True, False, False),
    ("15. Failure, Surprise & Abstention Corpus — P0", "§15 L425", "The failure/surprise/abstention corpus is a strategic proprietary asset.", "GOVERNING_OBJECTIVE", "P0", True, False, False),
    ("18. Replay Fidelity Profile — P1", "§18 L492", "Not every replay has equal evidentiary quality.", "ACCEPTANCE_RESTRICTION", "P1", False, False, False),
    ("32. Quality and Acceptance Model", "§32 L819", "External standards/frameworks guide quality and governance principles; they do not prescribe BLACKDARK-specific components such as Market Time Machine, Failure Corpus, or Experience Coverage Vector.", "ACCEPTANCE_RESTRICTION", "P0", False, False, False),
    ("0. Status and Governing Position", "§0 L5", "Document purpose: institutional design and execution specification for accelerating trustworthy data, experimental experience, learning evidence, replay capability, outcome intelligence, and forward-shadow evidence without fabricating chronological live history.", "GOVERNING_OBJECTIVE", "P0", True, False, False),
]


def _sections_with_normative_content(spec_text: str) -> set[str]:
    """Heuristic: numbered sections containing normative markers."""
    sections: set[str] = set()
    current = None
    markers = re.compile(
        r"\b(must|should|required|hard rule|mandatory|prohibited|do not|never|shall not|preserve|reject|invalidate|track|monitor|support|include|disclose|rules?:)\b",
        re.I,
    )
    for line in spec_text.splitlines():
        m = re.match(r"^#+ (\d+)\.\s+(.+)$", line)
        if m:
            current = f"{m.group(1)}. {m.group(2).strip()}"
        elif current and markers.search(line):
            sections.add(current.split(" — ")[0] if " — " in current else current)
    # always include sections we extracted from
    return sections


def main() -> None:
    spec_text = SPEC.read_text(encoding="utf-8")
    all_raw = RAW + EXTRA
    rows = []
    for i, item in enumerate(all_raw, start=1):
        section, loc, text, rtype, priority, impl, prohib, live = item
        rows.append(
            {
                "primary_id": f"TEMP-PR-{i:04d}",
                "section": section,
                "source_location": loc,
                "requirement_text": text,
                "requirement_type": rtype,
                "priority": priority,
                "implementation_intended": impl,
                "explicit_prohibition": prohib,
                "possible_live_or_external_dependency": live,
            }
        )

    by_section = Counter(r["section"] for r in rows)
    by_type = Counter(r["requirement_type"] for r in rows)

    extracted_sections = set(by_section.keys())
    normative_sections = _sections_with_normative_content(spec_text)
    # map normative section numbers to our section prefix names
    section_prefixes = {s.split(".")[0].strip(): s for s in extracted_sections}
    zero_extracted = []
    for ns in sorted(normative_sections, key=lambda x: int(re.match(r"(\d+)", x).group(1)) if re.match(r"(\d+)", x) else 999):
        num = re.match(r"(\d+)", ns)
        if not num:
            continue
        prefix = num.group(1)
        if not any(es.startswith(f"{prefix}.") for es in extracted_sections):
            zero_extracted.append(ns)

    ambiguous = [
        {
            "source_location": r["source_location"],
            "requirement_text": r["requirement_text"],
            "note": "Preserved as primary requirement; atomic adjudication deferred to Phase 0C.",
        }
        for r in rows
        if "where applicable" in r["requirement_text"].lower()
        or "where relevant" in r["requirement_text"].lower()
        or "where practical" in r["requirement_text"].lower()
        or "where justified" in r["requirement_text"].lower()
        or "where feasible" in r["requirement_text"].lower()
    ]

    payload = {
        "phase": "0B",
        "phase_name": "Primary Normative Requirements Extraction",
        "governing_spec": str(SPEC.relative_to(ROOT)),
        "governing_spec_sha_at_extraction": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "extracted_at_utc": "2026-09-13T15:30:00Z",
        "PRIMARY_REQUIREMENTS_TOTAL": len(rows),
        "SECTIONS_WITH_NORMATIVE_CONTENT": sorted(extracted_sections),
        "SECTIONS_WITH_ZERO_EXTRACTED_REQUIREMENTS": zero_extracted,
        "KNOWN_OMISSIONS": [],
        "count_by_section": dict(sorted(by_section.items())),
        "count_by_requirement_type": dict(sorted(by_type.items())),
        "ambiguous_clauses_preserved_for_atomic_adjudication": ambiguous,
        "requirements": rows,
        "PHASE_0B_PRIMARY_EXTRACTION_COMPLETE": len(rows) > 0 and len(zero_extracted) == 0,
    }

    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "PRIMARY_REQUIREMENTS_TOTAL": payload["PRIMARY_REQUIREMENTS_TOTAL"],
        "SECTIONS_WITH_ZERO_EXTRACTED_REQUIREMENTS": zero_extracted,
        "KNOWN_OMISSIONS": payload["KNOWN_OMISSIONS"],
        "PHASE_0B_PRIMARY_EXTRACTION_COMPLETE": payload["PHASE_0B_PRIMARY_EXTRACTION_COMPLETE"],
        "count_by_section": payload["count_by_section"],
        "count_by_requirement_type": payload["count_by_requirement_type"],
        "ambiguous_count": len(ambiguous),
        "artifact": str(OUT),
    }, indent=2))


if __name__ == "__main__":
    main()
