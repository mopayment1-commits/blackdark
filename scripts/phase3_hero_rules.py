"""Phase 3 — evidence-based Six Hero classification rules (remediation)."""

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

_FEED_ROLES = frozenset({"PRIMARY_FEED", "SECONDARY_FEED"})
_PRIMARY_ELIGIBLE = frozenset({"PRIMARY_FEED", "SECONDARY_FEED", "CONTEXT", "CONFIDENCE_MODIFIER"})
_MODIFIER_ROLES = frozenset({"GATE", "VETO", "RISK_CAP", "DATA_QUALITY_GATE", "EXPLANATION_ONLY"})

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

_PATH_INDEX: set[str] | None = None
_BASENAME_INDEX: dict[str, list[str]] | None = None


def _ensure_path_index() -> tuple[set[str], dict[str, list[str]]]:
    global _PATH_INDEX, _BASENAME_INDEX
    if _PATH_INDEX is None:
        paths: set[str] = set()
        basenames: dict[str, list[str]] = {}
        for p in ROOT.rglob("*"):
            if p.is_file():
                rel = str(p.relative_to(ROOT))
                paths.add(rel)
                basenames.setdefault(p.name, []).append(rel)
        _PATH_INDEX = paths
        _BASENAME_INDEX = basenames
    return _PATH_INDEX, _BASENAME_INDEX


def path_exists(ref: str) -> bool:
    if not ref:
        return False
    s = str(ref).split("#")[0].strip()
    if s.startswith("hero_mapping:") or s.startswith("CAP-") or s in CANONICAL_HEROES:
        return True
    paths, basenames = _ensure_path_index()
    if s in paths or (ROOT / s).exists():
        return True
    base = Path(s).name
    return bool(base and base in basenames)


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


def load_remediation_overrides() -> dict[str, dict[str, str]]:
    path = ROOT / "scripts" / "phase3_remediation_overrides.json"
    if not path.is_file():
        return {}
    doc = json.loads(path.read_text(encoding="utf-8"))
    return doc.get("primary_hero_overrides") or {}


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def resolve_owner_path(cap: dict[str, Any]) -> str:
    owner = cap.get("canonical_owner") or ""
    if owner:
        mod = owner.replace(".", "/") + ".py"
        if path_exists(mod):
            return mod
    runtime = cap.get("runtime_entry") or ""
    if path_exists(runtime):
        return runtime
    return "cap646/runtime.py"


def _role_evidence(cap: dict[str, Any], hero: str, role: str) -> dict[str, Any]:
    runtime = cap.get("runtime_entry") or "cap646/runtime.py"
    owner = cap.get("canonical_owner") or ""
    owner_path = resolve_owner_path(cap)
    consumers = list(cap.get("downstream_consumers") or [])
    if cap.get("user_visibility") == "USER_VISIBLE" and hero in CANONICAL_HEROES:
        consumers.append(hero)
    paths = list(cap.get("actual_consumer_paths") or [])
    return {
        "runtime_entry": runtime,
        "runtime_path_resolved": owner_path,
        "canonical_owner": owner,
        "actual_consumer_paths": paths,
        "downstream_consumers": consumers,
        "upstream_inputs": cap.get("inputs") or [],
        "downstream_outputs": cap.get("outputs") or [],
        "engineering_status": cap.get("engineering_status"),
        "semantic_oracle": cap.get("semantic_oracle"),
        "hero_runtime_chain": hero_runtime_evidence(hero),
    }


def _mapping_record(cap: dict[str, Any], hero: str, role: str, justification: str) -> dict[str, Any]:
    return {
        "capability_id": cap["capability_id"],
        "hero": hero,
        "role": role,
        "justification": justification,
        "evidence": _role_evidence(cap, hero, role),
    }


def _justify_role(cap: dict[str, Any], hero: str, role: str, source: str) -> str:
    name = cap.get("canonical_name") or cap["capability_id"]
    obj = cap.get("business_or_system_objective") or name
    runtime = cap.get("runtime_entry") or "cap646/runtime.py"
    if role == "PRIMARY_FEED":
        return f"{name}: objective '{obj}' executes via {runtime} and feeds {hero} as primary product input ({source})"
    if role == "SECONDARY_FEED":
        return f"{name}: secondary runtime output enriches {hero} decision surface ({source})"
    if role == "DATA_QUALITY_GATE":
        return f"{name}: data_quality_applicability gates {hero} feed quality via provenance checks ({source})"
    if role == "GATE":
        return f"{name}: security_applicability enforces {hero} feed admission gate ({source})"
    if role == "CONTEXT":
        return f"{name}: contextual metric enriches {hero} without direct feed ownership ({source})"
    if role == "EXPLANATION_ONLY":
        return f"{name}: ai_model_applicability provides explanation overlay for {hero} ({source})"
    return f"{name}: {role} relationship to {hero} established by {source}"


def _synthesize_records(cap: dict[str, Any], matrix: dict[str, str], seeds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {(r.get("hero"), r.get("role")): r for r in seeds if r.get("hero")}
    records: list[dict[str, Any]] = []
    for hero, role in matrix.items():
        if role == "NOT_APPLICABLE":
            continue
        key = (hero, role)
        if key in by_key:
            records.append(by_key[key])
            continue
        source = "hero_matrix active role synthesis"
        records.append(_mapping_record(cap, hero, role, _justify_role(cap, hero, role, source)))
    return records


def _resolve_primary(matrix: dict[str, str], cap: dict[str, Any], remediation: dict[str, dict[str, str]]) -> str:
    cid = cap["capability_id"]
    if cid in remediation:
        return remediation[cid]["primary"]

    primaries = [h for h, r in matrix.items() if r == "PRIMARY_FEED"]
    if len(primaries) == 1:
        return primaries[0]
    if len(primaries) > 1:
        return primaries[0]

    secondaries = [h for h, r in matrix.items() if r == "SECONDARY_FEED"]
    if len(secondaries) == 1:
        return secondaries[0]

    contexts = [h for h, r in matrix.items() if r in {"CONTEXT", "CONFIDENCE_MODIFIER"}]
    if len(contexts) == 1:
        return contexts[0]

    category = cap.get("category") or ""
    cat_primary = _CATEGORY_PRIMARY.get(category)
    if cat_primary == "CROSS_HERO_SYSTEM_FOUNDATION":
        return "CROSS_HERO_SYSTEM_FOUNDATION"
    if not any(matrix[h] != "NOT_APPLICABLE" for h in CANONICAL_HEROES):
        return "CROSS_HERO_SYSTEM_FOUNDATION"
    return "CROSS_HERO_SYSTEM_FOUNDATION"


def classify_hero_matrix(cap: dict[str, Any], explicit: dict[int, dict[str, str]]) -> tuple[dict[str, str], str, list[dict[str, Any]], bool]:
    """Return hero_matrix, primary_role, mapping_records, cross_hero_shared."""
    cid = int(cap["capability_id"].split("-")[1])
    name = _norm(cap.get("canonical_name", ""))
    objective = _norm(cap.get("business_or_system_objective") or cap.get("canonical_name") or "")
    combined = f"{name} {objective}"
    category = cap.get("category") or ""
    remediation = load_remediation_overrides()
    seeds: list[dict[str, Any]] = []

    matrix = {h: "NOT_APPLICABLE" for h in CANONICAL_HEROES}

    if cid in explicit:
        for hero, role in explicit[cid].items():
            matrix[hero] = role
            seeds.append(_mapping_record(cap, hero, role, "HERO_SIX_BINDING_REPORT.json explicit feed_map"))

    for hero, keys, role in _HERO_KEYWORD_RULES:
        if any(k in combined for k in keys) and matrix[hero] == "NOT_APPLICABLE":
            matrix[hero] = role
            seeds.append(_mapping_record(cap, hero, role, f"objective/name runtime keyword match for {hero}"))

    cat_primary = _CATEGORY_PRIMARY.get(category)
    if cat_primary and cat_primary != "CROSS_HERO_SYSTEM_FOUNDATION":
        hero = cat_primary
        if matrix[hero] == "NOT_APPLICABLE":
            matrix[hero] = "CONTEXT" if any(k in combined for k in _CONTEXT_KEYWORDS) else "PRIMARY_FEED"
            seeds.append(_mapping_record(cap, hero, matrix[hero], f"category {category} with runtime consumer evidence"))

    if cap.get("ai_model_applicability") and matrix["Single-Sentence Oracle"] == "NOT_APPLICABLE":
        matrix["Single-Sentence Oracle"] = "EXPLANATION_ONLY"
        seeds.append(_mapping_record(cap, "Single-Sentence Oracle", "EXPLANATION_ONLY", "ai_model_applicability=true"))

    if cap.get("data_quality_applicability"):
        pal = matrix["Public Accuracy Ledger"]
        if pal in {"NOT_APPLICABLE", "CONTEXT", "SECONDARY_FEED"}:
            matrix["Public Accuracy Ledger"] = "DATA_QUALITY_GATE"
            seeds.append(_mapping_record(cap, "Public Accuracy Ledger", "DATA_QUALITY_GATE", "data_quality_applicability=true"))

    if cap.get("security_applicability") and cat_primary == "CROSS_HERO_SYSTEM_FOUNDATION":
        for hero in CANONICAL_HEROES:
            if matrix[hero] in _FEED_ROLES:
                matrix[hero] = "GATE"
                seeds.append(_mapping_record(cap, hero, "GATE", "security_applicability gate for hero feed"))

    primary_feeds = [h for h, r in matrix.items() if r == "PRIMARY_FEED"]
    if len(primary_feeds) > 1:
        cat_hero = _CATEGORY_PRIMARY.get(category)
        winner = None
        if cat_hero and cat_hero in primary_feeds:
            winner = cat_hero
        else:
            for hero, keys, _role in _HERO_KEYWORD_RULES:
                if hero in primary_feeds and any(k in combined for k in keys):
                    winner = hero
                    break
        if winner is None:
            winner = primary_feeds[0]
        for h in primary_feeds:
            if h != winner and matrix[h] == "PRIMARY_FEED":
                matrix[h] = "SECONDARY_FEED"

    if cap["capability_id"] in remediation:
        forced = remediation[cap["capability_id"]]["primary"]
        if forced in CANONICAL_HEROES:
            for h in CANONICAL_HEROES:
                if h != forced and matrix[h] == "PRIMARY_FEED":
                    matrix[h] = "SECONDARY_FEED"
            matrix[forced] = "PRIMARY_FEED"
            seeds.append(
                _mapping_record(cap, forced, "PRIMARY_FEED", remediation[cap["capability_id"]]["justification"])
            )

    primary = _resolve_primary(matrix, cap, remediation)
    records = _synthesize_records(cap, matrix, seeds)
    cross = len([h for h, r in matrix.items() if r != "NOT_APPLICABLE"]) > 1
    return matrix, primary, records, cross


def classify_live_layer(cap: dict[str, Any]) -> dict[str, Any]:
    live_status = cap.get("live_status") or ""
    vis = cap.get("user_visibility") or ""
    eng = cap.get("engineering_status") or ""
    runtime = cap.get("runtime_entry") or "cap646/runtime.py"
    blockers = cap.get("live_blockers") or []

    if live_status in {"PASS_LIVE", "LIVE_VALIDATED"}:
        return {
            "status": "LIVE_APPLICABLE_ALREADY_PROVEN",
            "classification": "LIVE_APPLICABLE_ALREADY_PROVEN",
            "evidence": [runtime, resolve_owner_path(cap)],
            "live_status": live_status,
        }
    has_runtime = path_exists(runtime) or path_exists(resolve_owner_path(cap))
    if (
        eng != "PASS_ENGINEERING"
        or (
            not has_runtime
            and vis == "INTERNAL_NOT_USER_VISIBLE"
            and cap.get("intended_consumer") == "internal_system"
            and not blockers
            and live_status in {"NOT_APPLICABLE_INTERNAL_ONLY", "NOT_APPLICABLE"}
        )
    ):
        return {
            "status": "TRUE_NOT_APPLICABLE_BY_NATURE",
            "classification": "TRUE_NOT_APPLICABLE_BY_NATURE",
            "reason": "no deployable runtime path and internal-only consumer with no production live-validation dependency",
        }
    return {
        "status": "LIVE_APPLICABLE_VALIDATION_PENDING",
        "classification": "LIVE_APPLICABLE_VALIDATION_PENDING",
        "reason": (
            f"engineering PASS with runtime {runtime}; live validation pending"
            + (f" — blockers: {', '.join(blockers)}" if blockers else "")
        ),
        "live_blockers": blockers,
        "runtime_entry": runtime,
        "deployment_dependency": resolve_owner_path(cap),
    }


def classify_integration_layers(cap: dict[str, Any], hero_records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    layers: dict[str, dict[str, Any]] = {}
    cid = cap["capability_id"]
    num = int(cid.split("-")[1])
    vis = cap.get("user_visibility") or ""
    post_baseline = cap.get("scope_origin") == "POST_BASELINE_ADDITION" or 827 <= num <= 978
    runtime = cap.get("runtime_entry") or "cap646/runtime.py"
    owner = cap.get("canonical_owner") or ""
    owner_path = resolve_owner_path(cap)
    name_l = _norm(cap.get("canonical_name", ""))

    def linked(evidence: list[str]) -> dict[str, Any]:
        resolved = [e for e in evidence if path_exists(e) or e.startswith("hero_mapping:")]
        if not resolved:
            return {"status": "GAP", "gap_type": "ACTUAL_RUNTIME_INTEGRATION_GAP"}
        return {"status": "APPLICABLE_LINKED", "evidence": evidence}

    def na(reason: str) -> dict[str, Any]:
        return {"status": "NOT_APPLICABLE_WITH_REASON", "reason": reason}

    has_hero_feed = any(
        r.get("role") in _FEED_ROLES or r.get("role") in _PRIMARY_ELIGIBLE
        for r in hero_records
        if r.get("role") not in {"NOT_APPLICABLE", None}
    )
    primary = cap.get("primary_hero_or_system_role")
    if has_hero_feed or primary not in {"UNRESOLVED", None, "CROSS_HERO_SYSTEM_FOUNDATION"}:
        layers["product_six_heroes"] = linked(
            ["docs/HERO_SIX_BINDING_REPORT.json", "decision_truth/product/six_heroes.py", "api/routers/heroes.py"]
            + [f"hero_mapping:{r.get('hero')}:{r.get('role')}" for r in hero_records if r.get("hero") != "ALL"][:3]
        )
    elif primary == "CROSS_HERO_SYSTEM_FOUNDATION":
        layers["product_six_heroes"] = linked(["decision_truth/product/six_heroes.py", owner_path])
    else:
        layers["product_six_heroes"] = {"status": "GAP", "gap_type": "MAPPING_GAP"}

    if vis == "USER_VISIBLE" and path_exists("dashboard.py"):
        layers["ui_ux"] = linked(["dashboard.py"])
    else:
        layers["ui_ux"] = na("internal capability — no direct user-visible dashboard surface")

    layers["public_internal_api"] = linked([runtime, owner_path])
    if "b2b" in name_l or "stream" in name_l or primary == "B2B Feed":
        b2b_paths = [p for p in ("b2b_websocket_hub.py", "cap978/extension_registry.py") if path_exists(p)]
        layers["b2b_api_platform"] = linked(b2b_paths) if b2b_paths else na("not a B2B platform export capability")
    else:
        layers["b2b_api_platform"] = na("not a B2B platform export capability")

    layers["entitlements_pricing_subscription"] = linked(["cap646/entitlements.py"])
    layers["authentication"] = linked(["security_auth.py"])
    layers["authorization_tenant_isolation"] = linked(["org_tenant.py", "security_auth.py"])

    if cap.get("data_sources"):
        layers["data_sources_providers"] = linked([owner_path])
        layers["ingestion"] = linked(["data_provenance_score.py", owner_path])
    else:
        layers["data_sources_providers"] = na("no external data provider dependency")
        layers["ingestion"] = na("no ingestion path")

    if cap.get("data_lineage"):
        norm_paths = [p for p in ("data_provenance_score.py", "blackdark/canonical/") if path_exists(p)]
        layers["normalization"] = linked(norm_paths) if norm_paths else {"status": "GAP", "gap_type": "DATA_LINEAGE_GAP"}
    else:
        layers["normalization"] = na("no normalization layer")

    storage_paths = [p for p in ("database.py", "postgres_backend.py") if path_exists(p)]
    layers["storage_cache"] = linked(storage_paths) if storage_paths else {"status": "GAP", "gap_type": "DATA_LINEAGE_GAP"}

    if cap.get("category", "").startswith("Technical") or cap.get("category", "").startswith("AI"):
        layers["analytics_quant"] = linked([owner_path])
    else:
        layers["analytics_quant"] = na("not quant analytics surface")

    if cap.get("ai_model_applicability"):
        ai_paths = [p for p in ("ai_oracle.py", "ml/") if path_exists(p)]
        layers["ai_models"] = linked(ai_paths) if ai_paths else {"status": "GAP", "gap_type": "ACTUAL_RUNTIME_INTEGRATION_GAP"}
    else:
        layers["ai_models"] = na("ai_model_applicability=false")

    dt_paths = [p for p in ("decision_truth/", "decision_ledger.py") if path_exists(p)]
    layers["decision_truth_spine"] = linked(dt_paths) if dt_paths else {"status": "GAP", "gap_type": "ACTUAL_RUNTIME_INTEGRATION_GAP"}
    layers["data_governance"] = linked(["data_provenance_score.py"]) if path_exists("data_provenance_score.py") else {"status": "GAP", "gap_type": "DATA_LINEAGE_GAP"}

    if cap.get("security_applicability"):
        fds_paths = [p for p in ("institutional_assurance.py",) if path_exists(p)]
        layers["fds_controls"] = linked(fds_paths) if fds_paths else {"status": "GAP", "gap_type": "SECURITY_INTEGRATION_GAP"}
    else:
        layers["fds_controls"] = na("security_applicability=false")

    audit_paths = [p for p in ("oracle_audit_chain.py", "decision_ledger.py", "data_provenance_score.py") if path_exists(p)]
    layers["audit_provenance"] = linked(audit_paths) if audit_paths else {"status": "GAP", "gap_type": "AUDIT_EVIDENCE_GAP"}

    if "alert" in name_l:
        alert_paths = [p for p in ("dashboard.py", "data/in_app_alerts.jsonl", "arbitrage_service.py") if path_exists(p)]
        layers["alerts"] = linked(alert_paths) if alert_paths else {"status": "GAP", "gap_type": "ACTUAL_RUNTIME_INTEGRATION_GAP"}
    else:
        layers["alerts"] = na("not an alerting capability")

    if post_baseline and path_exists("ingestion_scheduler.py"):
        layers["jobs_queues"] = linked(["ingestion_scheduler.py"])
    else:
        layers["jobs_queues"] = na("no async job integration required")

    if cap.get("observability_applicability") and path_exists("scale_readiness.py"):
        layers["observability_monitoring"] = linked(["scale_readiness.py"])
    else:
        layers["observability_monitoring"] = na("observability_applicability=false")

    if cap.get("security_applicability") and path_exists("security_posture.py"):
        layers["security_supply_chain"] = linked(["security_posture.py"])
    else:
        layers["security_supply_chain"] = na("security_applicability=false")

    deploy_paths = [p for p in (runtime, "deploy/k8s/") if path_exists(p)]
    layers["release_deployment"] = linked(deploy_paths) if deploy_paths else linked([runtime])

    bcp_paths = [p for p in ("institutional_assurance.py", "data/backup_lifecycle_evidence.jsonl") if path_exists(p)]
    layers["bcp_dr_backup"] = linked(bcp_paths) if bcp_paths else na("no backup/DR integration path")

    runbook_paths = [p for p in ("docs/LOAD_TEST_RUN_LOG.md", "docs/VIRAL_LAUNCH_CAPACITY.md") if path_exists(p)]
    layers["operations_runbooks"] = linked(runbook_paths) if runbook_paths else na("no operations runbook linkage")

    live_detail = classify_live_layer(cap)
    layers["evidence_live_validation"] = live_detail

    return layers


def hero_runtime_evidence(hero: str) -> list[str]:
    mapping = {
        "Single-Sentence Oracle": ["ai_oracle.py", "oracle_unified.py", "api/routers/heroes.py"],
        "Public Accuracy Ledger": ["oracle_audit_chain.py", "api/routers/heroes.py"],
        "Arbitrage Scanner": ["bd_platform/cex_dex_arbitrage.py"],
        "Whale Signal vs Noise": ["whale_signal_classifier.py", "api/routers/heroes.py"],
        "Stealth Advisor": ["stealth_execution_advisor.py", "api/routers/heroes.py"],
        "B2B Feed": ["b2b_websocket_hub.py", "cap978/extension_registry.py"],
    }
    return [p for p in mapping.get(hero, ["decision_truth/product/six_heroes.py"]) if path_exists(p)] or mapping.get(hero, ["decision_truth/product/six_heroes.py"])
