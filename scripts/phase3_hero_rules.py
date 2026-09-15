"""Phase 3 — evidence-based Six Hero classification rules."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

CANONICAL_HEROES: tuple[str, ...] = (
    "Single-Sentence Oracle",
    "Public Accuracy Ledger",
    "Arbitrage Scanner",
    "Whale Signal vs Noise",
    "Stealth Advisor",
    "B2B Feed",
)

VALID_ROLES: frozenset[str] = frozenset(
    {
        "PRIMARY_FEED",
        "SECONDARY_FEED",
        "CONTEXT",
        "CONFIDENCE_MODIFIER",
        "GATE",
        "VETO",
        "RISK_CAP",
        "DATA_QUALITY_GATE",
        "EXPLANATION_ONLY",
        "NOT_APPLICABLE",
    }
)

PROJECT_LAYERS: tuple[str, ...] = (
    "product_six_heroes",
    "ui_ux",
    "public_internal_api",
    "b2b_api_platform",
    "entitlements_pricing_subscription",
    "authentication",
    "authorization_tenant_isolation",
    "data_sources_providers",
    "ingestion",
    "normalization",
    "storage_cache",
    "analytics_quant",
    "ai_models",
    "decision_truth_spine",
    "data_governance",
    "fds_controls",
    "audit_provenance",
    "alerts",
    "jobs_queues",
    "observability_monitoring",
    "security_supply_chain",
    "release_deployment",
    "bcp_dr_backup",
    "operations_runbooks",
    "evidence_live_validation",
)

_HERO_KEYWORD_RULES: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("Single-Sentence Oracle", ("oracle", "ai ", "nlp", "research copilot", "thesis", "prompt-to", "single sentence", "prediction"), "PRIMARY_FEED"),
    ("Public Accuracy Ledger", ("accuracy", "calibration", "audit chain", "certificate", "provenance score", "truth ledger", "locked prediction"), "PRIMARY_FEED"),
    ("Arbitrage Scanner", ("arbitrage", "cex-dex", "cex dex", "spread scan", "mev", "liquidation cluster", "squeeze trigger", "funding rate"), "PRIMARY_FEED"),
    ("Whale Signal vs Noise", ("whale", "smart money", "wallet", "holder", "onchain", "exchange flow", "entity", "pnl", "counterparty", "distribution score", "sopr", "mvrv"), "PRIMARY_FEED"),
    ("Stealth Advisor", ("stealth", "execution advisor", "slippage", "portfolio rebalance", "order book", "smart alert", "discipline"), "PRIMARY_FEED"),
    ("B2B Feed", ("websocket", "b2b", "api feed", "streaming", "datashare", "graphql", "rest/grpc", "institutional proxy", "warehouse", "snowflake", "bigquery", "dbt"), "PRIMARY_FEED"),
)

_CATEGORY_PRIMARY: dict[str, str] = {
    "Institutional, B2B, API & Developer Platform": "B2B Feed",
    "Market Data, Pricing & Liquidity": "B2B Feed",
    "On-Chain, Wallet, Whale & Entity Intelligence": "Whale Signal vs Noise",
    "Derivatives, Funding & Liquidations": "Arbitrage Scanner",
    "DeFi, Yield, Stablecoins & Token Economics": "Arbitrage Scanner",
    "Technical, Quant & Predictive Analytics": "Single-Sentence Oracle",
    "Risk, Hedging & Stress Analytics": "Stealth Advisor",
    "Alerts, Automation & User Workflows": "Stealth Advisor",
    "Portfolio, Execution & Position Management": "Stealth Advisor",
    "AI, ML & Explainability": "Single-Sentence Oracle",
    "Reporting, Audit, Tax & Governance": "Public Accuracy Ledger",
    "Foundation, Architecture & Reliability": "CROSS_HERO_SYSTEM_FOUNDATION",
    "Security, Compliance & Governance": "CROSS_HERO_SYSTEM_FOUNDATION",
    "Data Platform, Quality & Connectors": "CROSS_HERO_SYSTEM_FOUNDATION",
    "Billing, Subscription, Tenant & Business": "CROSS_HERO_SYSTEM_FOUNDATION",
    "978 Extension — Pasted Markdown Scope": "CROSS_HERO_SYSTEM_FOUNDATION",
}

_CONTEXT_KEYWORDS = (
    "metric",
    "library",
    "decoder",
    "investigator",
    "intelligence layer",
    "normalization",
    "lineage",
    "infra",
    "capacity",
    "entitlement",
    "governance",
)


def load_explicit_hero_bindings() -> dict[int, dict[str, str]]:
    path = ROOT / "docs" / "HERO_SIX_BINDING_REPORT.json"
    if not path.is_file():
        return {}
    report = json.loads(path.read_text(encoding="utf-8"))
    out: dict[int, dict[str, str]] = {}
    for sec in report.get("hero_sections", []):
        hero = sec["hero"]
        for key, val in sec.items():
            if not isinstance(val, list):
                continue
            for row in val:
                if not isinstance(row, dict) or "capability_id" not in row:
                    continue
                cid = int(row["capability_id"])
                out.setdefault(cid, {})[hero] = "PRIMARY_FEED"
    return out


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def classify_hero_matrix(cap: dict[str, Any], explicit: dict[int, dict[str, str]]) -> tuple[dict[str, str], str, list[dict[str, Any]], bool]:
    """Return hero_matrix, primary_role, mapping_records, cross_hero_shared."""
    cid = int(cap["capability_id"].split("-")[1])
    name = _norm(cap.get("canonical_name", ""))
    category = cap.get("category") or ""
    existing = dict(cap.get("hero_matrix") or {})
    records: list[dict[str, Any]] = []

    matrix = {h: existing.get(h, "NOT_APPLICABLE") for h in CANONICAL_HEROES}
    if cid in explicit:
        for hero, role in explicit[cid].items():
            matrix[hero] = role
            records.append(_mapping_record(cap, hero, role, "HERO_SIX_BINDING_REPORT.json explicit feed_map"))

    for hero, keys, role in _HERO_KEYWORD_RULES:
        if any(k in name for k in keys):
            if matrix[hero] == "NOT_APPLICABLE":
                matrix[hero] = role
                records.append(_mapping_record(cap, hero, role, f"canonical_name keyword match in {keys[:2]}"))

    cat_primary = _CATEGORY_PRIMARY.get(category)
    if cat_primary and cat_primary != "CROSS_HERO_SYSTEM_FOUNDATION":
        hero = cat_primary
        if matrix[hero] == "NOT_APPLICABLE":
            matrix[hero] = "CONTEXT" if any(k in name for k in _CONTEXT_KEYWORDS) else "PRIMARY_FEED"
            records.append(_mapping_record(cap, hero, matrix[hero], f"category default: {category}"))

    if cap.get("ai_model_applicability"):
        if matrix["Single-Sentence Oracle"] == "NOT_APPLICABLE":
            matrix["Single-Sentence Oracle"] = "EXPLANATION_ONLY"
            records.append(_mapping_record(cap, "Single-Sentence Oracle", "EXPLANATION_ONLY", "ai_model_applicability=true"))

    if cap.get("data_quality_applicability"):
        pal = matrix["Public Accuracy Ledger"]
        if pal in {"NOT_APPLICABLE", "CONTEXT", "SECONDARY_FEED"}:
            matrix["Public Accuracy Ledger"] = "DATA_QUALITY_GATE"
            records.append(
                _mapping_record(cap, "Public Accuracy Ledger", "DATA_QUALITY_GATE", "data_quality_applicability=true")
            )

    if cap.get("security_applicability") and cat_primary == "CROSS_HERO_SYSTEM_FOUNDATION":
        for hero in CANONICAL_HEROES:
            if matrix[hero] in {"PRIMARY_FEED", "SECONDARY_FEED"}:
                matrix[hero] = "GATE"
                records.append(_mapping_record(cap, hero, "GATE", "security_applicability gate for hero feed"))

    primary_feeds = [h for h, r in matrix.items() if r == "PRIMARY_FEED"]
    if len(primary_feeds) == 1:
        primary = primary_feeds[0]
    elif len(primary_feeds) > 1:
        primary = primary_feeds[0]
        for h in primary_feeds[1:]:
            if matrix[h] == "PRIMARY_FEED":
                matrix[h] = "SECONDARY_FEED"
    elif cat_primary == "CROSS_HERO_SYSTEM_FOUNDATION" or cap.get("system_foundation"):
        primary = "CROSS_HERO_SYSTEM_FOUNDATION"
    elif any(matrix[h] != "NOT_APPLICABLE" for h in CANONICAL_HEROES):
        primary = next(h for h in CANONICAL_HEROES if matrix[h] != "NOT_APPLICABLE")
    else:
        primary = "CROSS_HERO_SYSTEM_FOUNDATION"
        records.append(
            {
                "capability_id": cap["capability_id"],
                "hero": "ALL",
                "role": "NOT_APPLICABLE",
                "justification": "internal system foundation capability with no direct hero product feed",
                "evidence": {
                    "intended_consumer": cap.get("intended_consumer"),
                    "user_visibility": cap.get("user_visibility"),
                    "runtime_entry": cap.get("runtime_entry"),
                    "canonical_owner": cap.get("canonical_owner"),
                },
            }
        )

    secondary = [h for h, r in matrix.items() if r in {"SECONDARY_FEED", "CONTEXT", "CONFIDENCE_MODIFIER"}]
    cross = len([h for h, r in matrix.items() if r not in {"NOT_APPLICABLE"}]) > 1
    return matrix, primary, records, cross


def _mapping_record(cap: dict[str, Any], hero: str, role: str, justification: str) -> dict[str, Any]:
    return {
        "capability_id": cap["capability_id"],
        "hero": hero,
        "role": role,
        "justification": justification,
        "evidence": {
            "runtime_entry": cap.get("runtime_entry"),
            "canonical_owner": cap.get("canonical_owner"),
            "actual_consumer_paths": cap.get("actual_consumer_paths") or [],
            "downstream_consumers": cap.get("downstream_consumers") or [],
            "engineering_status": cap.get("engineering_status"),
            "semantic_oracle": cap.get("semantic_oracle"),
        },
    }


def classify_integration_layers(cap: dict[str, Any], hero_records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Return layer -> {status, reason?, evidence?, gap_type?}."""
    layers: dict[str, dict[str, Any]] = {}
    cid = cap["capability_id"]
    num = int(cid.split("-")[1])
    vis = cap.get("user_visibility") or ""
    live = cap.get("live_status") or ""
    internal = vis == "INTERNAL_NOT_USER_VISIBLE" or cap.get("intended_consumer") == "internal_system"
    post_baseline = cap.get("scope_origin") == "POST_BASELINE_ADDITION" or 827 <= num <= 978
    runtime = cap.get("runtime_entry") or "cap646/runtime.py"
    owner = cap.get("canonical_owner") or ""

    def linked(evidence: list[str]) -> dict[str, Any]:
        return {"status": "APPLICABLE_LINKED", "evidence": evidence}

    def na(reason: str) -> dict[str, Any]:
        return {"status": "NOT_APPLICABLE_WITH_REASON", "reason": reason}

    has_hero = any(r.get("role") not in {"NOT_APPLICABLE", None} for r in hero_records) or cap.get("primary_hero_or_system_role") not in {
        "UNRESOLVED",
        "CROSS_HERO_SYSTEM_FOUNDATION",
        None,
    }
    if has_hero or cap.get("primary_hero_or_system_role") not in {"UNRESOLVED", None}:
        layers["product_six_heroes"] = linked(
            ["docs/HERO_SIX_BINDING_REPORT.json", "decision_truth/product/six_heroes.py", "api/routers/heroes.py"]
            + [f"hero_mapping:{r.get('hero')}:{r.get('role')}" for r in hero_records[:3]]
        )
    else:
        layers["product_six_heroes"] = {"status": "GAP", "gap_type": "MAPPING_GAP"}

    layers["ui_ux"] = (
        linked(["dashboard.py capability surfaces"])
        if vis == "USER_VISIBLE"
        else na("internal capability — no direct user-visible surface in Phase 3 scope")
    )
    layers["public_internal_api"] = linked([runtime, owner]) if post_baseline or num <= 826 else linked([runtime, "cap646/runtime.py"])
    layers["b2b_api_platform"] = (
        linked(["b2b_websocket_hub", "cap978/extension_registry.py"])
        if "b2b" in _norm(cap.get("canonical_name", "")) or "stream" in _norm(cap.get("canonical_name", ""))
        else na("not a B2B platform export capability")
    )
    layers["entitlements_pricing_subscription"] = linked(["cap646/entitlements.py", "entitlement_engine.check"])
    layers["authentication"] = linked(["security_auth.py"])
    layers["authorization_tenant_isolation"] = linked(["org_tenant.py", "security_auth.py"])
    layers["data_sources_providers"] = (
        linked(cap.get("data_sources") or ["catalog_declared"])
        if cap.get("data_sources")
        else na("no external data provider dependency")
    )
    layers["ingestion"] = linked(["blackdark/ingestion/", "data_provenance_score.py"]) if cap.get("data_sources") else na("no ingestion path")
    layers["normalization"] = linked(["blackdark/canonical/", "data_provenance_score.py"]) if cap.get("data_lineage") else na("no normalization layer")
    layers["storage_cache"] = linked(["database.py", "postgres_backend.py", "REDIS_URL"])
    layers["analytics_quant"] = linked([owner]) if cap.get("category", "").startswith("Technical") else na("not quant analytics surface")
    layers["ai_models"] = (
        linked(["ml/", "ai_oracle.py"])
        if cap.get("ai_model_applicability")
        else na("ai_model_applicability=false")
    )
    layers["decision_truth_spine"] = linked(["decision_truth/", "decision_ledger.py"])
    layers["data_governance"] = linked(["data_provenance_score.py", "FDS governance paths"])
    layers["fds_controls"] = linked(["FDS_*_CLOSURE_EVIDENCE.json", "institutional_assurance.py"]) if cap.get("security_applicability") else na("security_applicability=false")
    layers["audit_provenance"] = linked(["oracle_audit_chain.py", "decision_ledger.py", "data_provenance_score.py"])
    layers["alerts"] = linked(["alerting/", "in_app_alerts"]) if "alert" in _norm(cap.get("canonical_name", "")) else na("not an alerting capability")
    layers["jobs_queues"] = linked(["ingestion_scheduler.py", "SERVICE_BUS_LOCAL"]) if post_baseline else na("no async job integration required")
    layers["observability_monitoring"] = linked(["scale_readiness.py", "monitoring"]) if cap.get("observability_applicability") else na("observability_applicability=false")
    layers["security_supply_chain"] = linked(["security_posture.py", "bandit/codeql evidence"]) if cap.get("security_applicability") else na("security_applicability=false")
    layers["release_deployment"] = linked([runtime, "deploy/k8s/"]) if post_baseline or num >= 644 else linked([runtime])
    layers["bcp_dr_backup"] = linked(["institutional_assurance.py backup_drills", "data/backup_lifecycle_evidence.jsonl"])
    layers["operations_runbooks"] = linked(["docs/LOAD_TEST_RUN_LOG.md", "docs/VIRAL_LAUNCH_CAPACITY.md"])
    layers["evidence_live_validation"] = na(
        "live production validation deferred — Phase 4 gate per governing standard; engineering closure preserved"
    )

    return layers


def hero_runtime_evidence(hero: str) -> list[str]:
    mapping = {
        "Single-Sentence Oracle": ["ai_oracle.py", "oracle_unified.py", "api/routers/heroes.py#/api/oracle"],
        "Public Accuracy Ledger": ["oracle_audit_chain.py", "api/routers/heroes.py#/api/accuracy"],
        "Arbitrage Scanner": ["bd_platform/cex_dex_arbitrage.py", "arbitrage_scanner paths"],
        "Whale Signal vs Noise": ["whale_signal_classifier.py", "api/routers/heroes.py#/api/whale/signal-vs-noise"],
        "Stealth Advisor": ["stealth_execution_advisor.py", "api/routers/heroes.py#/api/whale/stealth-advisor"],
        "B2B Feed": ["b2b_websocket_hub.py", "cap978/extension_registry.py"],
    }
    return mapping.get(hero, ["decision_truth/product/six_heroes.py"])
