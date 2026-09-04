# BATCH04_INSTITUTIONAL_PENTAGONAL_BUILD

**Generated:** 2026-09-04T07:45:50.531518+00:00 | **Commit:** `41d15a900ea7` | **Scope:** Batch04 IDs 151–200
**Classification:** BUILD PHASE OPEN — **NOT** LOCAL_GOVERNANCE_COMPLETE
**Acceptance source:** `BATCH04_ACCEPTANCE_151_200.json` (pre_probe, ISO 29148)

هذه المرحلة = بناء spine + قبول مسبق + اختبارات محلية فقط. لا إعلان اكتمال حوكمة · لا Batch05 · لا جاهزية حية 100%.

---

## Structural Blockers (hard stop)

| Blocker | Pair | Status |
|---------|------|--------|
| BLOCKER-159-103 | 159 ↔ 103 | canonical #103 PENDING_SCOPE_REALIGNMENT |
| BLOCKER-183-130 | 183 ↔ 130 | canonical #130 PENDING + semantic gap |

ADR: `docs/ADR_BATCH04_CANONICAL_BLOCKERS_103_130.md`

---

## Status Table (151–200)

| Bucket | Count |
|--------|------:|
| NOT_COMPLETE (dedicated batch04 spine) | 49 |
| OVERLAP-PARTIAL (batch01 #175) | 1 |
| PENDING_CANONICAL_AUDIT subset | 2 | 159, 183 |
| PRODUCTION-ALIGNED | 0 |

```
batch04_independent = 0
progress_826        = 148
domain_rules_all_pass = 49/50
```

---

## RTM — every ID

| ID | Closure | Spine | Domain pass | Blocker |
|----|---------|-------|-------------|---------|
| 151 | NOT_COMPLETE | batch04 | 7/7 | — |
| 152 | NOT_COMPLETE | batch04 | 4/4 | — |
| 153 | NOT_COMPLETE | batch04 | 4/4 | — |
| 154 | NOT_COMPLETE | batch04 | 4/4 | — |
| 155 | NOT_COMPLETE | batch04 | 4/4 | — |
| 156 | NOT_COMPLETE | batch04 | 4/4 | — |
| 157 | NOT_COMPLETE | batch04 | 4/4 | — |
| 158 | NOT_COMPLETE | batch04 | 4/4 | — |
| 159 | NOT_COMPLETE | batch04 | 5/5 | BLOCKER-159-103 |
| 160 | NOT_COMPLETE | batch04 | 4/4 | — |
| 161 | NOT_COMPLETE | batch04 | 4/4 | — |
| 162 | NOT_COMPLETE | batch04 | 4/4 | — |
| 163 | NOT_COMPLETE | batch04 | 4/4 | — |
| 164 | NOT_COMPLETE | batch04 | 4/4 | — |
| 165 | NOT_COMPLETE | batch04 | 4/4 | — |
| 166 | NOT_COMPLETE | batch04 | 4/4 | — |
| 167 | NOT_COMPLETE | batch04 | 4/4 | — |
| 168 | NOT_COMPLETE | batch04 | 4/4 | — |
| 169 | NOT_COMPLETE | batch04 | 4/4 | — |
| 170 | NOT_COMPLETE | batch04 | 4/4 | — |
| 171 | NOT_COMPLETE | batch04 | 4/4 | — |
| 172 | NOT_COMPLETE | batch04 | 4/4 | — |
| 173 | NOT_COMPLETE | batch04 | 4/4 | — |
| 174 | NOT_COMPLETE | batch04 | 4/4 | — |
| 175 | OVERLAP-PARTIAL | batch01 | 5/5 | — |
| 176 | NOT_COMPLETE | batch04 | 4/4 | — |
| 177 | NOT_COMPLETE | batch04 | 4/4 | — |
| 178 | NOT_COMPLETE | batch04 | 4/4 | — |
| 179 | NOT_COMPLETE | batch04 | 4/4 | — |
| 180 | NOT_COMPLETE | batch04 | 4/4 | — |
| 181 | NOT_COMPLETE | batch04 | 4/4 | — |
| 182 | NOT_COMPLETE | batch04 | 4/4 | — |
| 183 | NOT_COMPLETE | batch04 | 3/4 | BLOCKER-183-130 |
| 184 | NOT_COMPLETE | batch04 | 4/4 | — |
| 185 | NOT_COMPLETE | batch04 | 4/4 | — |
| 186 | NOT_COMPLETE | batch04 | 4/4 | — |
| 187 | NOT_COMPLETE | batch04 | 4/4 | — |
| 188 | NOT_COMPLETE | batch04 | 4/4 | — |
| 189 | NOT_COMPLETE | batch04 | 4/4 | — |
| 190 | NOT_COMPLETE | batch04 | 4/4 | — |
| 191 | NOT_COMPLETE | batch04 | 4/4 | — |
| 192 | NOT_COMPLETE | batch04 | 4/4 | — |
| 193 | NOT_COMPLETE | batch04 | 4/4 | — |
| 194 | NOT_COMPLETE | batch04 | 4/4 | — |
| 195 | NOT_COMPLETE | batch04 | 4/4 | — |
| 196 | NOT_COMPLETE | batch04 | 4/4 | — |
| 197 | NOT_COMPLETE | batch04 | 4/4 | — |
| 198 | NOT_COMPLETE | batch04 | 4/4 | — |
| 199 | NOT_COMPLETE | batch04 | 4/4 | — |
| 200 | NOT_COMPLETE | batch04 | 4/4 | — |

---

## Pentagonal per ID (columns 6–10)

### ID 151 — Quarterly Protocol Performance Reports

- **Col 6 (25010):** Quarterly Protocol Performance Reports | binding:cap646/batch04_dedicated.py:_cap151 | Binding _cap151 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'reporting_period', 'quarter_label', 'protocol_symbol', 'protocol_tvl_usd']
- **Col 7 (29148):** success:pass; surface:pass; quarterly_protocol_performance_reports.ok:pass; quarterly_protocol_performance_reports.feature_ref:pass; quarterly_protocol_performance_reports.reporting_period:pass; quarterly_protocol_performance_reports.protocol_tvl_usd:pass; quarterly_protocol_performance_reports.protocol_performance.quarterly_summary:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/151 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 2.9ms / 2000ms (analysis) within=True

### ID 152 — Governance & Proposal Intelligence

- **Col 6 (25010):** Governance & Proposal Intelligence | binding:cap646/batch04_dedicated.py:_cap152 | Binding _cap152 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'rule_based', 'ai_classification', 'data_freshness', 'governance_proposals']
- **Col 7 (29148):** success:pass; surface:pass; governance_proposal_intelligence.ok:pass; governance_proposal_intelligence.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/152 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 0.6ms / 2000ms (analysis) within=True

### ID 153 — Project Monitoring Coverage Registry

- **Col 6 (25010):** Project Monitoring Coverage Registry | binding:cap646/batch04_dedicated.py:_cap153 | Binding _cap153 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'rule_based', 'ai_classification', 'data_freshness', 'coverage_registry']
- **Col 7 (29148):** success:pass; surface:pass; project_monitoring_coverage_registry.ok:pass; project_monitoring_coverage_registry.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/153 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 41.6ms / 2000ms (analysis) within=True

### ID 154 — AI Crypto Copilot

- **Col 6 (25010):** AI Crypto Copilot | binding:cap646/batch04_dedicated.py:_cap154 | Binding _cap154 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'rule_based', 'ai_classification', 'data_freshness', 'copilot_status']
- **Col 7 (29148):** success:pass; surface:pass; ai_crypto_copilot.ok:pass; ai_crypto_copilot.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/154 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 0.9ms / 5000ms (ai_interpretation) within=True

### ID 155 — AI Deep Research

- **Col 6 (25010):** AI Deep Research | binding:cap646/batch04_dedicated.py:_cap155 | Binding _cap155 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'rule_based', 'ai_classification', 'data_freshness', 'research_depth']
- **Col 7 (29148):** success:pass; surface:pass; ai_deep_research.ok:pass; ai_deep_research.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/155 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 144.0ms / 5000ms (ai_interpretation) within=True

### ID 156 — Crypto Knowledge Graph

- **Col 6 (25010):** Crypto Knowledge Graph | binding:cap646/batch04_dedicated.py:_cap156 | Binding _cap156 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'rule_based', 'ai_classification', 'data_freshness', 'graph_nodes']
- **Col 7 (29148):** success:pass; surface:pass; crypto_knowledge_graph.ok:pass; crypto_knowledge_graph.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/156 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 3.0ms / 2000ms (analysis) within=True

### ID 157 — Research Library

- **Col 6 (25010):** Research Library | binding:cap646/batch04_dedicated.py:_cap157 | Binding _cap157 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'rule_based', 'ai_classification', 'data_freshness', 'research_items']
- **Col 7 (29148):** success:pass; surface:pass; research_library.ok:pass; research_library.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/157 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 267.1ms / 2000ms (analysis) within=True

### ID 158 — Institutional Research Feed

- **Col 6 (25010):** Institutional Research Feed | binding:cap646/batch04_dedicated.py:_cap158 | Binding _cap158 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'rule_based', 'ai_classification', 'data_freshness', 'feed_items']
- **Col 7 (29148):** success:pass; surface:pass; institutional_research_feed.ok:pass; institutional_research_feed.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/158 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 85.1ms / 500ms (direct_data) within=True

### ID 159 — API Data Platform

- **Col 6 (25010):** API Data Platform | binding:None:None | BLOCKER-159-103 owner decision: NOT_COMPLETE — no REUSED-LINK until #103 matures (Tolerate 2026-10-03)
- **Col 7 (29148):** success:pass; surface:pass; api_data_platform.canonical_overlap:pass; api_data_platform.canonical_status:pass; api_data_platform.institutional_api:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/159 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 0.1ms / 500ms (direct_data) within=True
- **Blocker:** Canonical #103 is OVERLAP-PARTIAL — REUSED-LINK for #159 suspended until maturity or DISTINCT ADR

### ID 160 — Pay-Per-Request Data Access

- **Col 6 (25010):** Pay-Per-Request Data Access | binding:cap646/batch04_dedicated.py:_cap160 | Binding _cap160 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'rule_based', 'ai_classification', 'data_freshness', 'pricing_model']
- **Col 7 (29148):** success:pass; surface:pass; pay_per_request_data_access.ok:pass; pay_per_request_data_access.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/160 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 0.1ms / 500ms (direct_data) within=True

### ID 161 — Institutional Data Delivery & Entitlements

- **Col 6 (25010):** Institutional Data Delivery & Entitlements | binding:None:None | Binding None returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'isolation', 'role_matrix', 'entitlements']
- **Col 7 (29148):** success:pass; surface:pass; institutional_data_delivery_entitlements.ok:pass; institutional_data_delivery_entitlements.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/161 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 1.9ms / 500ms (direct_data) within=True

### ID 162 — Evidence & Provenance Layer

- **Col 6 (25010):** Evidence & Provenance Layer | binding:None:None | Binding None returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'provenance', 'hot_storage']
- **Col 7 (29148):** success:pass; surface:pass; evidence_provenance_layer.ok:pass; evidence_provenance_layer.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/162 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 0.6ms / 500ms (direct_data) within=True

### ID 163 — Cross-Domain Research-to-Decision Intelligence

- **Col 6 (25010):** Cross-Domain Research-to-Decision Intelligence | binding:cap646/batch04_dedicated.py:_cap163 | Binding _cap163 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'rule_based', 'ai_classification', 'data_freshness', 'research_summary']
- **Col 7 (29148):** success:pass; surface:pass; cross_domain_research_to_decision_intelligence.ok:pass; cross_domain_research_to_decision_intelligence.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/163 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 121.1ms / 5000ms (ai_interpretation) within=True

### ID 164 — Token Unlock Actionability Score

- **Col 6 (25010):** Token Unlock Actionability Score | binding:cap646/batch04_dedicated.py:_cap164 | Binding _cap164 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'rule_based', 'ai_classification', 'data_freshness', 'actionability_score']
- **Col 7 (29148):** success:pass; surface:pass; token_unlock_actionability_score.ok:pass; token_unlock_actionability_score.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/164 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 25.0ms / 500ms (direct_data) within=True

### ID 165 — Fundraising Momentum Score

- **Col 6 (25010):** Fundraising Momentum Score | binding:cap646/batch04_dedicated.py:_cap165 | Binding _cap165 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'rule_based', 'ai_classification', 'data_freshness', 'momentum_score']
- **Col 7 (29148):** success:pass; surface:pass; fundraising_momentum_score.ok:pass; fundraising_momentum_score.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/165 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 15.6ms / 500ms (direct_data) within=True

### ID 166 — Research Confidence Score

- **Col 6 (25010):** Research Confidence Score | binding:None:None | Binding None returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'confidence_score', 'research_status', 'insights_only']
- **Col 7 (29148):** success:pass; surface:pass; research_confidence_score.ok:pass; research_confidence_score.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/166 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 107.6ms / 2000ms (analysis) within=True

### ID 167 — Social Volume Intelligence

- **Col 6 (25010):** Social Volume Intelligence | binding:cap646/batch04_dedicated.py:_cap167 | Binding _cap167 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'rule_based', 'ai_classification', 'data_freshness', 'social_volume']
- **Col 7 (29148):** success:pass; surface:pass; social_volume_intelligence.ok:pass; social_volume_intelligence.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/167 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 0.6ms / 500ms (direct_data) within=True

### ID 168 — Social Dominance Intelligence

- **Col 6 (25010):** Social Dominance Intelligence | binding:cap646/batch04_dedicated.py:_cap168 | Binding _cap168 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'dominance_pct', 'social_volume', 'network_growth', 'metrics']
- **Col 7 (29148):** success:pass; surface:pass; social_dominance_intelligence.ok:pass; social_dominance_intelligence.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/168 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 0.7ms / 500ms (direct_data) within=True

### ID 169 — Unique Social Volume

- **Col 6 (25010):** Unique Social Volume | binding:cap646/batch04_dedicated.py:_cap169 | Binding _cap169 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'rule_based', 'ai_classification', 'data_freshness', 'unique_social_volume']
- **Col 7 (29148):** success:pass; surface:pass; unique_social_volume.ok:pass; unique_social_volume.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/169 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 0.5ms / 500ms (direct_data) within=True

### ID 170 — Trending Words

- **Col 6 (25010):** Trending Words | binding:cap646/batch04_dedicated.py:_cap170 | Binding _cap170 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'rule_based', 'ai_classification', 'data_freshness', 'trending_words']
- **Col 7 (29148):** success:pass; surface:pass; trending_words.ok:pass; trending_words.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/170 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 163.1ms / 500ms (direct_data) within=True

### ID 171 — Trending Coins

- **Col 6 (25010):** Trending Coins | binding:cap646/batch04_dedicated.py:_cap171 | Binding _cap171 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'trending_coins', 'trending_symbols', 'requested_symbol_rank', 'source']
- **Col 7 (29148):** success:pass; surface:pass; trending_coins.ok:pass; trending_coins.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/171 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 0.1ms / 500ms (direct_data) within=True

### ID 172 — Historical Crypto Trends

- **Col 6 (25010):** Historical Crypto Trends | binding:cap646/batch04_dedicated.py:_cap172 | Binding _cap172 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'rule_based', 'ai_classification', 'data_freshness', 'historical_trends']
- **Col 7 (29148):** success:pass; surface:pass; historical_crypto_trends.ok:pass; historical_crypto_trends.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/172 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 12.6ms / 500ms (direct_data) within=True

### ID 173 — Key Narratives Intelligence

- **Col 6 (25010):** Key Narratives Intelligence | binding:None:None | Binding None returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'key_narratives', 'narrative_count']
- **Col 7 (29148):** success:pass; surface:pass; key_narratives_intelligence.ok:pass; key_narratives_intelligence.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/173 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 132.0ms / 500ms (direct_data) within=True

### ID 174 — Alpha Narratives Intelligence

- **Col 6 (25010):** Alpha Narratives Intelligence | binding:None:None | Binding None returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'alpha_narratives', 'branding_status']
- **Col 7 (29148):** success:pass; surface:pass; alpha_narratives_intelligence.ok:pass; alpha_narratives_intelligence.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/174 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 133.9ms / 500ms (direct_data) within=True

### ID 175 — Social Sentiment Intelligence

- **Col 6 (25010):** Social Sentiment Intelligence | binding:None:None | PARTIAL_MISNAMED: catalog 'Social Sentiment Intelligence' vs implemented 'batch01 sentiment_ai gate (LEGACY_BATCH01_EXTENSION_IDS)'
- **Col 7 (29148):** success:pass; surface:pass; production_spine:pass; gate.asset:pass; context.sentiment_compound_index:pass | domain_status:COMPLETE | closure:OVERLAP-PARTIAL
- **Col 8 (29119):** /api/cap646/175 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 5.6ms / 500ms (direct_data) within=True

### ID 176 — Weighted Social Sentiment

- **Col 6 (25010):** Weighted Social Sentiment | binding:None:None | Binding None returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'weighted_sentiment', 'sentiment_weights', 'checks']
- **Col 7 (29148):** success:pass; surface:pass; weighted_social_sentiment.ok:pass; weighted_social_sentiment.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/176 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 2.4ms / 500ms (direct_data) within=True

### ID 177 — Social Sentiment Balance

- **Col 6 (25010):** Social Sentiment Balance | binding:None:None | Binding None returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'sentiment_balance', 'cost_breakdown']
- **Col 7 (29148):** success:pass; surface:pass; social_sentiment_balance.ok:pass; social_sentiment_balance.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/177 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 0.7ms / 500ms (direct_data) within=True

### ID 178 — Social Source Breakdown

- **Col 6 (25010):** Social Source Breakdown | binding:None:None | Binding None returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'source_breakdown', 'scenario_count']
- **Col 7 (29148):** success:pass; surface:pass; social_source_breakdown.ok:pass; social_source_breakdown.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/178 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 0.5ms / 500ms (direct_data) within=True

### ID 179 — Development Activity Intelligence

- **Col 6 (25010):** Development Activity Intelligence | binding:None:None | Binding None returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'dev_activity_score', 'widgets']
- **Col 7 (29148):** success:pass; surface:pass; development_activity_intelligence.ok:pass; development_activity_intelligence.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/179 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 1.3ms / 500ms (direct_data) within=True

### ID 180 — Development Activity Contributors

- **Col 6 (25010):** Development Activity Contributors | binding:None:None | Binding None returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'contributor_count', 'whale_flows']
- **Col 7 (29148):** success:pass; surface:pass; development_activity_contributors.ok:pass; development_activity_contributors.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/180 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 0.6ms / 500ms (direct_data) within=True

### ID 181 — IC Committee Packets Status

- **Col 6 (25010):** IC Committee Packets Status | binding:None:None | Binding None returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'ecosystem_score', 'committee_packets']
- **Col 7 (29148):** success:pass; surface:pass; ecosystem_development_dashboard.ok:pass; ecosystem_development_dashboard.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/181 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 0.5ms / 500ms (direct_data) within=True

### ID 182 — White-Label Infrastructure Status

- **Col 6 (25010):** White-Label Infrastructure Status | binding:None:None | Binding None returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'activity_change_pct', 'dev_activity_delta']
- **Col 7 (29148):** success:pass; surface:pass; developer_activity_change_detection.ok:pass; developer_activity_change_detection.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/182 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 0.5ms / 500ms (direct_data) within=True

### ID 183 — Whale Transaction Intelligence

- **Col 6 (25010):** Whale Transaction Intelligence | binding:cap646/batch04_dedicated.py:_cap183 | BLOCKER-183-130 owner decision: DISTINCT whale payload; #130 PRODUCTION-ALIGNED in Batch03 untouched
- **Col 7 (29148):** success:pass; surface:pass; whale_transaction.risk_score:pass; classification:FAIL | domain_status:NOT_COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/183 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 0.2ms / 500ms (direct_data) within=True
- **Blocker:** DISTINCT-only Option B approved — no REUSED-LINK to PRODUCTION-ALIGNED #130

### ID 184 — Whale & Shark Holder Cohorts

- **Col 6 (25010):** Whale & Shark Holder Cohorts | binding:cap646/batch04_dedicated.py:_cap184 | Binding _cap184 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'rule_based', 'ai_classification', 'data_freshness', 'holder_cohorts']
- **Col 7 (29148):** success:pass; surface:pass; whale_shark_holder_cohorts.ok:pass; whale_shark_holder_cohorts.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/184 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 89.1ms / 500ms (direct_data) within=True

### ID 185 — Top Holders Intelligence

- **Col 6 (25010):** Top Holders Intelligence | binding:cap646/batch04_dedicated.py:_cap185 | Binding _cap185 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'rule_based', 'ai_classification', 'data_freshness', 'top_holders']
- **Col 7 (29148):** success:pass; surface:pass; top_holders_intelligence.ok:pass; top_holders_intelligence.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/185 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 85.1ms / 500ms (direct_data) within=True

### ID 186 — Historical Wallet Balance Tool

- **Col 6 (25010):** Historical Wallet Balance Tool | binding:cap646/batch04_dedicated.py:_cap186 | Binding _cap186 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'address', 'chain', 'balance_history', 'current_balance_eth']
- **Col 7 (29148):** success:pass; surface:pass; historical_wallet_balance_tool.ok:pass; historical_wallet_balance_tool.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/186 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 705.2ms / 500ms (direct_data) within=False

### ID 187 — Exchange Inflow Intelligence

- **Col 6 (25010):** Exchange Inflow Intelligence | binding:cap646/batch04_dedicated.py:_cap187 | Binding _cap187 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'vendor_status', 'status', 'vendor', 'vendor_label']
- **Col 7 (29148):** success:pass; surface:pass; exchange_inflow_intelligence.ok:pass; exchange_inflow_intelligence.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/187 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 1.5ms / 500ms (direct_data) within=True

### ID 188 — Exchange Outflow Intelligence

- **Col 6 (25010):** Exchange Outflow Intelligence | binding:cap646/batch04_dedicated.py:_cap188 | Binding _cap188 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'vendor_status', 'status', 'vendor', 'vendor_label']
- **Col 7 (29148):** success:pass; surface:pass; exchange_outflow_intelligence.ok:pass; exchange_outflow_intelligence.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/188 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 0.0ms / 500ms (direct_data) within=True

### ID 189 — Exchange Netflow Intelligence

- **Col 6 (25010):** Exchange Netflow Intelligence | binding:cap646/batch04_dedicated.py:_cap189 | Binding _cap189 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'rule_based', 'ai_classification', 'data_freshness', 'exchange']
- **Col 7 (29148):** success:pass; surface:pass; exchange_netflow_intelligence.ok:pass; exchange_netflow_intelligence.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/189 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 0.8ms / 500ms (direct_data) within=True

### ID 190 — Exchange Supply / Balance Intelligence

- **Col 6 (25010):** Exchange Supply / Balance Intelligence | binding:cap646/batch04_dedicated.py:_cap190 | Binding _cap190 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'vendor_status', 'status', 'vendor', 'vendor_label']
- **Col 7 (29148):** success:pass; surface:pass; exchange_supply_balance_intelligence.ok:pass; exchange_supply_balance_intelligence.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/190 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 0.0ms / 500ms (direct_data) within=True

### ID 191 — Exchange User Activity

- **Col 6 (25010):** Exchange User Activity | binding:None:None | Binding None returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'user_activity_score', 'withdrawal_alerts']
- **Col 7 (29148):** success:pass; surface:pass; exchange_user_activity.ok:pass; exchange_user_activity.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/191 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 1.5ms / 500ms (direct_data) within=True

### ID 192 — Network Activity Intelligence

- **Col 6 (25010):** Network Activity Intelligence | binding:cap646/batch04_dedicated.py:_cap192 | Binding _cap192 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'rule_based', 'ai_classification', 'data_freshness', 'network_activity']
- **Col 7 (29148):** success:pass; surface:pass; network_activity_intelligence.ok:pass; network_activity_intelligence.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/192 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 1.1ms / 500ms (direct_data) within=True

### ID 193 — Transaction Volume Intelligence

- **Col 6 (25010):** Transaction Volume Intelligence | binding:cap646/batch04_dedicated.py:_cap193 | Binding _cap193 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'rule_based', 'ai_classification', 'data_freshness', 'transaction_volume']
- **Col 7 (29148):** success:pass; surface:pass; transaction_volume_intelligence.ok:pass; transaction_volume_intelligence.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/193 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 627.1ms / 500ms (direct_data) within=False

### ID 194 — NVT Intelligence

- **Col 6 (25010):** NVT Intelligence | binding:cap646/batch04_dedicated.py:_cap194 | Binding _cap194 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'rule_based', 'ai_classification', 'data_freshness', 'nvt_ratio']
- **Col 7 (29148):** success:pass; surface:pass; nvt_intelligence.ok:pass; nvt_intelligence.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/194 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 605.3ms / 500ms (direct_data) within=False

### ID 195 — MVRV Intelligence

- **Col 6 (25010):** MVRV Intelligence | binding:cap646/batch04_dedicated.py:_cap195 | Binding _cap195 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'rule_based', 'ai_classification', 'data_freshness', 'mvrv_ratio']
- **Col 7 (29148):** success:pass; surface:pass; mvrv_intelligence.ok:pass; mvrv_intelligence.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/195 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 12.2ms / 500ms (direct_data) within=True

### ID 196 — Realized Cap / Realized Value Intelligence

- **Col 6 (25010):** Realized Cap / Realized Value Intelligence | binding:cap646/batch04_dedicated.py:_cap196 | Binding _cap196 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'rule_based', 'ai_classification', 'data_freshness', 'realized_cap_usd']
- **Col 7 (29148):** success:pass; surface:pass; realized_cap_realized_value_intelligence.ok:pass; realized_cap_realized_value_intelligence.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/196 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 11.9ms / 500ms (direct_data) within=True

### ID 197 — Daily Active Addresses

- **Col 6 (25010):** Daily Active Addresses | binding:cap646/batch04_dedicated.py:_cap197 | Binding _cap197 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'rule_based', 'ai_classification', 'data_freshness', 'active_addresses']
- **Col 7 (29148):** success:pass; surface:pass; daily_active_addresses.ok:pass; daily_active_addresses.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/197 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 0.8ms / 500ms (direct_data) within=True

### ID 198 — Age Consumed / Dormancy Intelligence

- **Col 6 (25010):** Age Consumed / Dormancy Intelligence | binding:cap646/batch04_dedicated.py:_cap198 | Binding _cap198 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'rule_based', 'ai_classification', 'data_freshness', 'dormancy_proxy_score']
- **Col 7 (29148):** success:pass; surface:pass; age_consumed_dormancy_intelligence.ok:pass; age_consumed_dormancy_intelligence.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/198 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 12.5ms / 500ms (direct_data) within=True

### ID 199 — Mean Dollar Invested Age

- **Col 6 (25010):** Mean Dollar Invested Age | binding:cap646/batch04_dedicated.py:_cap199 | Binding _cap199 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'rule_based', 'ai_classification', 'data_freshness', 'invested_age_proxy_days']
- **Col 7 (29148):** success:pass; surface:pass; mean_dollar_invested_age.ok:pass; mean_dollar_invested_age.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/199 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 11.8ms / 500ms (direct_data) within=True

### ID 200 — Token Circulation Intelligence

- **Col 6 (25010):** Token Circulation Intelligence | binding:cap646/batch04_dedicated.py:_cap200 | Binding _cap200 returns goal-specific keys: ['ok', 'feature_ref', 'symbol', 'catalog_goal', 'rule_based', 'ai_classification', 'data_freshness', 'circulation_rate']
- **Col 7 (29148):** success:pass; surface:pass; token_circulation_intelligence.ok:pass; token_circulation_intelligence.feature_ref:pass | domain_status:COMPLETE | closure:NOT_COMPLETE
- **Col 8 (29119):** /api/cap646/200 | local_COMPLETE:True | live:AWAITING_DEPLOY — Railway not validated for batch04 spine
- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)
- **Col 10 (LOCAL_REVIEW):** LOCAL_REVIEW — Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR
- **Latency (local):** 33.5ms / 500ms (direct_data) within=True

---

## Triple-match guard

Proof: `BATCH04_RULE_COUNT_ASSERT_PROOF.txt` — acceptance_count == results == rules_total for all 50 IDs.

## Heroes (batch04 independent)

**batch04_independent = 0** — N/A per hero engine item-by-item until PA closures exist.
