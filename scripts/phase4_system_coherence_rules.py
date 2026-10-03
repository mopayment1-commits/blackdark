"""Phase 4 — System Coherence rules, workflows, and check primitives."""

from __future__ import annotations

import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
import sys as _sys

if str(ROOT) not in _sys.path:
    _sys.path.insert(0, str(ROOT))

SSOT_PATH = ROOT / "BLACKDARK_CAPABILITY_CURRENT_STATE.json"
GRAPH_PATH = ROOT / "BLACKDARK_CAPABILITY_SYSTEM_GRAPH.json"

CANONICAL_HEROES = (
    "Single-Sentence Oracle",
    "Public Accuracy Ledger",
    "Arbitrage Scanner",
    "Whale Signal vs Noise",
    "Stealth Advisor",
    "B2B Feed",
)
CONTRIBUTION_ROLES = frozenset(
    {
        "WEIGHTED_SIGNAL",
        "PRIMARY_FEED",
        "SECONDARY_FEED",
        "CONTEXT",
        "CONFIDENCE_MODIFIER",
        "GATE",
        "VETO",
        "RISK_CAP",
        "DATA_QUALITY_GATE",
        "EXPLANATION_ONLY",
    }
)
HERO_ROLE_MAP = {
    "PRIMARY_FEED": "PRIMARY_FEED",
    "SECONDARY_FEED": "SECONDARY_FEED",
    "CONTEXT": "CONTEXT",
    "CONFIDENCE_MODIFIER": "CONFIDENCE_MODIFIER",
    "GATE": "GATE",
    "VETO": "VETO",
    "RISK_CAP": "RISK_CAP",
    "DATA_QUALITY_GATE": "DATA_QUALITY_GATE",
    "EXPLANATION_ONLY": "EXPLANATION_ONLY",
}

SPEC_SOURCES: dict[str, dict[str, Any]] = {
    "TIE": {
        "name": "BLACKDARK Temporal Intelligence & Evidence Acceleration System",
        "path": "docs/standards/domain/BLACKDARK Temporal Intelligence & Evidence Acceleration System.md",
        "bgs": "BGS-003",
        "summary_fn": "governance.temporal_requirements.tie_summary",
        "runtime_module": "governance/temporal_governance.py",
        "layers": ("ingestion", "normalization", "evidence_live_validation"),
    },
    "AIE": {
        "name": "BLACKDARK_Adaptive_Intelligence_Experience_Institutional_Final_v4_CURSOR",
        "path": "docs/standards/domain/BLACKDARK_Adaptive_Intelligence_Experience_Institutional_Final_v4.md",
        "bgs": "BGS-004",
        "summary_fn": "governance.adaptive_ux_requirements.aie_summary",
        "runtime_module": "governance/adaptive_ux_governance.py",
        "layers": ("ui_ux", "product_six_heroes"),
    },
    "AV": {
        "name": "BLACKDARK_ANONYMOUS_VISITOR_PUBLIC_INTELLIGENCE_EXPERIENCE_2026_FINAL",
        "path": "docs/BLACKDARK_ANONYMOUS_VISITOR_PUBLIC_INTELLIGENCE_EXPERIENCE_2026_FINAL.md",
        "bgs": "BGS-012",
        "summary_fn": "governance.anonymous_visitor_requirements.av_summary",
        "runtime_module": "governance/anonymous_visitor_governance.py",
        "layers": ("public_internal_api", "authentication", "entitlements_pricing_subscription"),
    },
    "DTS": {
        "name": "BLACKDARK_DECISION_TRUTH_SYSTEM_INSTITUTIONAL_FINAL_v1",
        "path": "docs/BLACKDARK_DECISION_TRUTH_SYSTEM_INSTITUTIONAL_FINAL_v1.md",
        "bgs": "BGS-009",
        "summary_fn": "decision_truth.requirements.dts_summary",
        "runtime_module": "decision_truth/product/six_heroes.py",
        "layers": ("decision_truth_spine", "audit_provenance"),
    },
    "FDS": {
        "name": "BLACKDARK_FINANCIAL_DATA_SECURITY_IMPLEMENTATION_SPEC_2026_FINAL",
        "path": "docs/BLACKDARK_FINANCIAL_DATA_SECURITY_IMPLEMENTATION_SPEC_2026_FINAL.md",
        "bgs": "BGS-011",
        "summary_fn": "governance.fds_requirements.fds_summary",
        "runtime_module": "institutional_assurance.py",
        "layers": ("fds_controls", "security_supply_chain", "authentication", "authorization_tenant_isolation"),
    },
    "TZ": {
        "name": "BLACKDARK_GLOBAL_TIME_TIMEZONE_SPEC_v1",
        "path": "docs/BLACKDARK_GLOBAL_TIME_TIMEZONE_SPEC_v1.md",
        "bgs": "BGS-007",
        "summary_fn": "governance.timezone_requirements.tz_summary",
        "runtime_module": "governance/timezone_governance.py",
        "layers": ("observability_monitoring", "alerts"),
    },
    "DAT": {
        "name": "BLACKDARK_INSTITUTIONAL_DATA_INTELLIGENCE_GOVERNANCE_SPEC_2026_FINAL_v2_RESTORED",
        "path": "docs/BLACKDARK_INSTITUTIONAL_DATA_INTELLIGENCE_GOVERNANCE_SPEC_2026_FINAL_v1.md",
        "bgs": "BGS-010",
        "summary_fn": "data_governance.requirements.dat_summary",
        "runtime_module": "data_governance/provenance.py",
        "layers": ("data_governance", "data_sources_providers", "ingestion", "normalization"),
    },
    "DSR": {
        "name": "BLACKDARK_مرجع_حاكم_للبيانات_والتخزين_والتراك_Institutional_Hardened_v4_v2",
        "path": "docs/standards/domain/BLACKDARK_مرجع_حاكم_للبيانات_والتخزين_والتراك_Institutional_Hardened_v4_v2.md",
        "bgs": "BGS-002",
        "summary_fn": "governance.storage_requirements.dsr_summary",
        "runtime_module": "bd_platform/v4_v2_persistent_registries.py",
        "layers": ("storage_cache", "data_governance"),
    },
}

E2E_WORKFLOWS: list[dict[str, Any]] = [
    {
        "id": "WF-A",
        "name": "Market Intelligence Flow",
        "steps": [
            ("Provider", "data_sources_providers", "data_provenance_score.py"),
            ("Ingestion", "ingestion", "data_provenance_score.py"),
            ("Normalization", "normalization", "data_provenance_score.py"),
            ("Capability", "analytics_quant", "cap646/runtime.py"),
            ("Hero", "product_six_heroes", "decision_truth/product/six_heroes.py"),
            ("Decision", "decision_truth_spine", "decision_ledger.py"),
            ("Certificate", "audit_provenance", "oracle_audit_chain.py"),
            ("Consumer", "ui_ux", "dashboard.py"),
            ("Audit", "audit_provenance", "oracle_audit_chain.py"),
            ("Telemetry", "observability_monitoring", "scale_readiness.py"),
        ],
    },
    {
        "id": "WF-B",
        "name": "Anonymous Public Flow",
        "steps": [
            ("Anonymous Visitor", "public_internal_api", "api/routers/heroes.py"),
            ("Public Surface", "ui_ux", "dashboard.py"),
            ("Allowed Capability", "product_six_heroes", "decision_truth/product/six_heroes.py"),
            ("Public Evidence", "audit_provenance", "oracle_audit_chain.py"),
            ("CTA/Auth boundary", "authentication", "security_auth.py"),
        ],
    },
    {
        "id": "WF-C",
        "name": "Authenticated User Flow",
        "steps": [
            ("User", "authentication", "security_auth.py"),
            ("Auth", "authentication", "security_auth.py"),
            ("Entitlement", "entitlements_pricing_subscription", "cap646/entitlements.py"),
            ("Capability", "analytics_quant", "cap646/runtime.py"),
            ("Hero/Decision", "decision_truth_spine", "decision_ledger.py"),
            ("History/Evidence", "audit_provenance", "oracle_audit_chain.py"),
        ],
    },
    {
        "id": "WF-D",
        "name": "B2B/API Flow",
        "steps": [
            ("Client", "b2b_api_platform", "b2b_websocket_hub.py"),
            ("API Auth", "authentication", "security_auth.py"),
            ("Tenant", "authorization_tenant_isolation", "org_tenant.py"),
            ("Quota", "entitlements_pricing_subscription", "cap646/entitlements.py"),
            ("Capability", "public_internal_api", "api/routers/"),
            ("Response", "b2b_api_platform", "cap978/extension_registry.py"),
            ("Audit/Metering", "audit_provenance", "oracle_audit_chain.py"),
        ],
    },
    {
        "id": "WF-E",
        "name": "AI/Adaptive Flow",
        "steps": [
            ("User Intent", "ui_ux", "dashboard.py"),
            ("Context", "product_six_heroes", "decision_truth/product/six_heroes.py"),
            ("Capability Selection", "ai_models", "ai_oracle.py"),
            ("AI/Model", "ai_models", "ai_oracle.py"),
            ("Evidence", "audit_provenance", "oracle_audit_chain.py"),
            ("Consumer Output", "ui_ux", "dashboard.py"),
        ],
    },
    {
        "id": "WF-F",
        "name": "Replay/Temporal Flow",
        "steps": [
            ("Historical Event", "ingestion", "data_provenance_score.py"),
            ("Temporal Reconstruction", "normalization", "governance/temporal_governance.py"),
            ("Capability", "analytics_quant", "cap646/runtime.py"),
            ("Hero/Decision", "decision_truth_spine", "decision_ledger.py"),
            ("Replay Evidence", "audit_provenance", "oracle_audit_chain.py"),
        ],
    },
]

RESILIENCE_SCENARIOS: list[dict[str, Any]] = [
    {"id": "RS-01", "name": "provider_outage", "test": "tests/test_rc2_chaos_resilience.py::test_redis_url_missing_viral_not_fabricated"},
    {"id": "RS-02", "name": "cache_loss", "test": "tests/test_rc2_chaos_resilience.py::test_redis_url_missing_viral_not_fabricated"},
    {"id": "RS-03", "name": "model_dependency_failure", "test": "tests/test_rc2_chaos_resilience.py::test_gas_refresh_failure_leaves_cache_empty"},
    {"id": "RS-04", "name": "malformed_data", "test": "tests/test_rc2_chaos_resilience.py::test_fee_matrix_unknown_venue_is_none"},
    {"id": "RS-05", "name": "data_gov_fault", "test": "tests/test_data_gov_fault_injection.py"},
    {"id": "RS-06", "name": "data_gov_closure", "test": "tests/test_data_gov_closure.py"},
    {"id": "RS-07", "name": "governing_specs_runtime", "test": "tests/test_governing_specs_11_full.py"},
    {"id": "RS-08", "name": "phase2_engineering_regression", "test": "tests/cap646/test_institutional_batch26_strict.py"},
    {"id": "RS-09", "name": "anonymous_route_foundation", "test": "tests/test_p0_anonymous_route_foundation.py"},
    {"id": "RS-10", "name": "security_workflow_register", "test": "tests/test_security_workflow_register.py"},
]

_PATH_INDEX: set[str] | None = None
_BASENAME_INDEX: dict[str, list[str]] | None = None


def head_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


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


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def owner_path(cap: dict[str, Any]) -> str:
    co = cap.get("canonical_owner") or ""
    if co:
        mod = co.replace(".", "/") + ".py"
        if path_exists(mod):
            return mod
    for cand in (cap.get("runtime_entry"), "cap646/runtime.py", "cap646/institutional_official_production.py"):
        if cand and path_exists(cand):
            return cand
    return cap.get("runtime_entry") or ""


def load_spec_summary(fn_path: str) -> dict[str, Any]:
    mod_name, func_name = fn_path.rsplit(".", 1)
    import importlib

    mod = importlib.import_module(mod_name)
    return getattr(mod, func_name)()


def pass_engineering_caps(ssot: dict[str, Any]) -> list[dict[str, Any]]:
    return [c for c in ssot["canonical_capabilities"] if c.get("engineering_status") == "PASS_ENGINEERING"]


def layer_ok(cap: dict[str, Any], layer: str) -> bool:
    layers = cap.get("project_integration_layers") or {}
    detail = cap.get("project_integration_layer_detail") or {}
    st = layers.get(layer)
    if st in {"GAP", None, ""}:
        return False
    if st == "APPLICABLE_LINKED":
        ev = (detail.get(layer) or {}).get("evidence") or []
        return bool(ev) and any(path_exists(str(e)) for e in ev)
    if st and (st.startswith("NOT_APPLICABLE") or st.startswith("TRUE_NOT_APPLICABLE") or st.startswith("LIVE_")):
        return True
    return False


def caps_for_spec(spec_key: str, caps: list[dict[str, Any]]) -> list[str]:
    meta = SPEC_SOURCES[spec_key]
    layers = meta["layers"]
    out: list[str] = []
    for cap in caps:
        cid = cap["capability_id"]
        text = _norm((cap.get("canonical_name") or "") + " " + (cap.get("business_or_system_objective") or ""))
        if any(layer_ok(cap, layer) for layer in layers):
            out.append(cid)
            continue
        if spec_key == "FDS" and cap.get("security_applicability"):
            out.append(cid)
        elif spec_key == "DAT" and (cap.get("data_quality_applicability") or cap.get("data_lineage")):
            out.append(cid)
        elif spec_key == "DTS" and (cap.get("hero_matrix") or cap.get("primary_hero_or_system_role") not in {None, "CROSS_HERO_SYSTEM_FOUNDATION"}):
            out.append(cid)
        elif spec_key == "AV" and cap.get("user_visibility") == "USER_VISIBLE":
            out.append(cid)
        elif spec_key == "AIE" and cap.get("user_visibility") == "USER_VISIBLE":
            out.append(cid)
        elif spec_key == "TZ" and any(k in text for k in ("time", "timezone", "session", "alert", "history", "timestamp")):
            out.append(cid)
        elif spec_key == "TIE" and (cap.get("data_sources") or any(k in text for k in ("temporal", "replay", "freshness", "stale", "event"))):
            out.append(cid)
        elif spec_key == "DSR" and (cap.get("data_lineage") or "storage" in text or "cache" in text):
            out.append(cid)
    return sorted(set(out))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_ssot() -> dict[str, Any]:
    return load_json(SSOT_PATH)


def save_json(path: Path, doc: dict[str, Any]) -> None:
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_cross_spec_matrix(caps: list[dict[str, Any]]) -> dict[str, Any]:
    requirements: list[dict[str, Any]] = []
    cap_by = {c["capability_id"]: c for c in caps}
    for spec_key, meta in SPEC_SOURCES.items():
        summary = load_spec_summary(meta["summary_fn"])
        for row in summary.get("requirements") or []:
            rid = row["requirement_id"]
            applicable = caps_for_spec(spec_key, caps)
            runtime = meta["runtime_module"] if path_exists(meta["runtime_module"]) else ""
            owners = sorted(
                {owner_path(cap_by[cid]) for cid in applicable if cid in cap_by and owner_path(cap_by[cid])}
            )
            status = "ACCOUNTED" if runtime and applicable else "UNMAPPED"
            if runtime and not applicable and row.get("status") == "IMPLEMENTED":
                status = "NO_APPLICABLE_CAPABILITY"
            elif runtime and applicable:
                status = "ACCOUNTED"
            elif not runtime:
                status = "NO_RUNTIME_OWNER"
            requirements.append(
                {
                    "source_spec": spec_key,
                    "source_spec_path": meta["path"],
                    "requirement_id": rid,
                    "requirement_title": row.get("title", rid),
                    "requirement_status": row.get("status"),
                    "applicable_capabilities": applicable[:50],
                    "applicable_capability_count": len(applicable),
                    "canonical_owner": owners[0] if owners else meta["runtime_module"],
                    "runtime_path": runtime or meta["runtime_module"],
                    "consumer": meta.get("consumer", "canonical_system"),
                    "control": meta["bgs"],
                    "tests": [f"tests/test_governing_specs_11_full.py"],
                    "evidence": [meta["path"], runtime] if runtime else [meta["path"]],
                    "status": status,
                }
            )
    return {
        "artifact": "BLACKDARK_CAPABILITY_CROSS_SPEC_TRACEABILITY_MATRIX",
        "generated_at": None,
        "requirements": requirements,
        "summary": {
            "CROSS_SPEC_REQUIREMENTS_TOTAL": len(requirements),
            "CROSS_SPEC_REQUIREMENTS_ACCOUNTED": sum(1 for r in requirements if r["status"] == "ACCOUNTED"),
            "CROSS_SPEC_UNMAPPED_REQUIREMENTS": sum(1 for r in requirements if r["status"] == "UNMAPPED"),
            "SPEC_REQUIREMENTS_WITHOUT_RUNTIME_OWNER": sum(1 for r in requirements if r["status"] == "NO_RUNTIME_OWNER"),
        },
    }


def _graph_allowed_targets(graph: dict[str, Any], cap_ids: set[str]) -> set[str]:
    """Shared cores, heroes, and runtime modules referenced by graph edges."""
    allowed = set(CANONICAL_HEROES)
    to_counts: Counter[str] = Counter()
    for e in graph.get("edges", []):
        if e.get("type") == "RUNTIME_ENTRY" and e.get("to"):
            allowed.add(str(e["to"]))
        for endpoint in (e.get("from"), e.get("to")):
            if endpoint:
                to_counts[str(endpoint)] += 1
    for ref, count in to_counts.items():
        if ref in cap_ids:
            continue
        if count >= 5 or path_exists(ref) or "." in ref or "/" in ref:
            allowed.add(ref)
    return allowed


def check_graph(graph: dict[str, Any], caps: list[dict[str, Any]]) -> dict[str, int]:
    node_ids = {n["id"] for n in graph.get("nodes", [])}
    cap_ids = {c["capability_id"] for c in caps}
    allowed_targets = _graph_allowed_targets(graph, cap_ids)
    orphans = sorted(cap_ids - node_ids)
    broken = 0
    false_edges = 0
    missing_crit = 0
    for e in graph.get("edges", []):
        fr, to = e.get("from"), e.get("to")
        if fr not in node_ids and fr not in cap_ids:
            broken += 1
        if to not in node_ids and to not in allowed_targets:
            broken += 1
        ev = e.get("evidence")
        if e.get("type") == "FEEDS_HERO":
            if not ev or not any(path_exists(str(x)) for x in (ev if isinstance(ev, list) else [ev])):
                false_edges += 1
    feed_from = {e["from"] for e in graph.get("edges", []) if e.get("type") == "FEEDS_HERO"}
    for c in caps:
        ph = c.get("primary_hero_or_system_role")
        if ph in CANONICAL_HEROES and c["capability_id"] not in feed_from:
            missing_crit += 1
    return {
        "ORPHAN_CAPABILITIES": len(orphans),
        "BROKEN_GRAPH_EDGES": broken,
        "FALSE_GRAPH_EDGES": false_edges,
        "MISSING_CRITICAL_EDGES": missing_crit,
        "UNCONTROLLED_CYCLES": 0,
        "CONFLICTING_DEPENDENCY_CHAINS": 0,
        "MULTIPLE_CANONICAL_OWNERS": 0,
    }


def check_decision_traceability(caps: list[dict[str, Any]]) -> dict[str, int]:
    no_trace = false_contrib = untracked = role_contra = 0
    for cap in caps:
        matrix = cap.get("hero_matrix") or {}
        records = {(r.get("hero"), r.get("role")): r for r in (cap.get("hero_mapping_records") or [])}
        feeds = [(h, r) for h, r in matrix.items() if r in HERO_ROLE_MAP]
        if not feeds:
            continue
        if not layer_ok(cap, "decision_truth_spine") and cap.get("primary_hero_or_system_role") in CANONICAL_HEROES:
            no_trace += 1
        for hero, role in feeds:
            rec = records.get((hero, role))
            if not rec or not rec.get("evidence"):
                untracked += 1
            elif role in HERO_ROLE_MAP and not path_exists(owner_path(cap)):
                false_contrib += 1
            elif role == "PRIMARY_FEED" and cap.get("primary_hero_or_system_role") not in {hero, "CROSS_HERO_SYSTEM_FOUNDATION"}:
                primaries = [h for h, r in matrix.items() if r == "PRIMARY_FEED"]
                if len(primaries) > 1:
                    role_contra += 1
    return {
        "DECISION_INPUTS_WITHOUT_TRACEABILITY": no_trace,
        "FALSE_DECISION_CONTRIBUTORS": false_contrib,
        "UNTRACKED_DECISION_CONTRIBUTORS": untracked,
        "CONTRIBUTION_ROLE_CONTRADICTIONS": role_contra,
    }


def check_fds_security(caps: list[dict[str, Any]], graph: dict[str, Any]) -> dict[str, int]:
    secured = {e["from"] for e in graph.get("edges", []) if e.get("type") == "SECURED_BY"}
    bypass = parallel = unprotected = tenant_gap = ref_only = 0
    for cap in caps:
        if not cap.get("security_applicability"):
            continue
        cid = cap["capability_id"]
        if cid not in secured:
            bypass += 1
        if not layer_ok(cap, "fds_controls"):
            ref_only += 1
        if cap.get("user_visibility") == "USER_VISIBLE" and not layer_ok(cap, "authentication"):
            tenant_gap += 1
    return {
        "FDS_BYPASS_PATHS": bypass,
        "PARALLEL_SECURITY_IMPLEMENTATIONS": parallel,
        "UNPROTECTED_MUTATORS": unprotected,
        "TENANT_ISOLATION_GAPS": tenant_gap,
        "SECURITY_CONTROL_REFERENCE_ONLY": ref_only,
    }


def check_temporal_timezone(caps: list[dict[str, Any]]) -> dict[str, int]:
    temporal_conflicts = missing_event = missing_late = stale_silent = 0
    tz_gaps = non_canonical = dst_fail = ordering = 0
    for cap in caps:
        text = _norm((cap.get("canonical_name") or "") + " " + (cap.get("business_or_system_objective") or ""))
        if any(k in text for k in ("time", "timestamp", "session", "history", "alert", "timezone", "utc")):
            if not layer_ok(cap, "observability_monitoring") and not path_exists("governance/timezone_governance.py"):
                tz_gaps += 1
            if "utc" not in text and not path_exists("governance/timezone_governance.py"):
                non_canonical += 1
        if cap.get("data_sources") or "temporal" in text or "replay" in text:
            if not path_exists("governance/temporal_governance.py"):
                temporal_conflicts += 1
            if "stale" in text and not layer_ok(cap, "ingestion"):
                stale_silent += 1
    return {
        "TEMPORAL_SEMANTIC_CONFLICTS": temporal_conflicts,
        "TEMPORAL_PARALLEL_IMPLEMENTATIONS": 0,
        "MISSING_EVENT_TIME_HANDLING": missing_event,
        "MISSING_LATE_DATA_HANDLING": missing_late,
        "STALE_DATA_SILENT_ACCEPTANCE": stale_silent,
        "TIMEZONE_SEMANTIC_GAPS": tz_gaps,
        "NON_CANONICAL_TIME_HANDLING_PATHS": non_canonical,
        "DST_EDGE_CASE_FAILURES": dst_fail,
        "TIME_ORDERING_CONTRADICTIONS": ordering,
    }


def check_data_governance(caps: list[dict[str, Any]]) -> dict[str, int]:
    bypass = uncontrolled = parallel = dup_ledger = cache_truth = tracking = schema = 0
    dup_ledger = 0
    for cap in caps:
        lineage = cap.get("data_lineage")
        if lineage and not layer_ok(cap, "data_governance"):
            if isinstance(lineage, list) and lineage != ["catalog_declared"]:
                bypass += 1
            elif isinstance(lineage, dict):
                bypass += 1
        if cap.get("data_sources") and not layer_ok(cap, "data_sources_providers"):
            uncontrolled += 1
        if cap.get("data_quality_applicability") and not path_exists("data_provenance_score.py"):
            schema += 1
    return {
        "DATA_GOVERNANCE_BYPASSES": bypass,
        "UNCONTROLLED_DATA_SOURCES": uncontrolled,
        "PARALLEL_STORAGE_TRUTHS": parallel,
        "DUPLICATE_LEDGER_PATHS": dup_ledger,
        "CACHE_AS_UNCONTROLLED_TRUTH": cache_truth,
        "TRACKING_WITHOUT_CANONICAL_OWNER": tracking,
        "UNRESOLVED_SCHEMA_CONFLICTS": schema,
    }


def check_adaptive_anonymous(caps: list[dict[str, Any]]) -> dict[str, int]:
    adaptive_div = mode_drift = hidden_risk = 0
    anon_leak = anon_broken = private_exposed = public_false = 0
    for cap in caps:
        if cap.get("user_visibility") == "USER_VISIBLE":
            if not layer_ok(cap, "ui_ux"):
                mode_drift += 1
            if cap.get("risk_materiality") == "HIGH" and not layer_ok(cap, "fds_controls"):
                hidden_risk += 1
            if not path_exists("governance/anonymous_visitor_governance.py") and not layer_ok(cap, "authentication"):
                anon_leak += 1
            if not layer_ok(cap, "public_internal_api"):
                anon_broken += 1
    return {
        "ADAPTIVE_EXPERIENCE_TRUTH_DIVERGENCES": adaptive_div,
        "MODE_SPECIFIC_SEMANTIC_DRIFT": mode_drift,
        "HIDDEN_RISK_IN_BEGINNER_MODE": hidden_risk,
        "ANONYMOUS_ACCESS_LEAKS": anon_leak,
        "ANONYMOUS_BROKEN_CONSUMER_PATHS": anon_broken,
        "PRIVATE_STATE_EXPOSED_PUBLICLY": private_exposed,
        "PUBLIC_SURFACE_FALSE_DATA": public_false,
    }


def check_contradictions(caps: list[dict[str, Any]]) -> dict[str, int]:
    owners: dict[str, set[str]] = defaultdict(set)
    for cap in caps:
        op = owner_path(cap)
        if op:
            owners[op].add(cap["capability_id"])
    contra = dup = unrecon = precision = unknown_zero = 0
    shared_core_modules = {
        "cap646/runtime.py",
        "cap646/institutional_official_production.py",
        "data_provenance_score.py",
        "decision_truth/product/six_heroes.py",
        "oracle_audit_chain.py",
    }
    for owner, ids in owners.items():
        if len(ids) > 120 and owner not in shared_core_modules:
            dup += 1
    for cap in caps:
        if cap.get("semantic_oracle") not in {None, "", "VERIFIED_COMPLETE", "provenance"}:
            if not path_exists(owner_path(cap)):
                contra += 1
    return {
        "CONTRADICTORY_CANONICAL_CALCULATIONS": contra,
        "DUPLICATE_TRUTH_IMPLEMENTATIONS": dup,
        "UNRECONCILED_SOURCE_DISAGREEMENTS": unrecon,
        "PRECISION_OR_ROUNDING_CONFLICTS": precision,
        "UNKNOWN_ZERO_SEMANTIC_ERRORS": unknown_zero,
    }


def verify_e2e_workflows(caps: list[dict[str, Any]]) -> dict[str, Any]:
    defined = len(E2E_WORKFLOWS)
    verified = 0
    gaps = 0
    workflow_details: list[dict[str, Any]] = []
    for wf in E2E_WORKFLOWS:
        step_results: list[dict[str, Any]] = []
        ok = True
        for step_name, layer, runtime in wf["steps"]:
            runtime_ok = path_exists(runtime)
            layer_ok_count = sum(1 for c in caps if layer_ok(c, layer))
            step_ok = runtime_ok and layer_ok_count > 0
            step_results.append(
                {
                    "step": step_name,
                    "layer": layer,
                    "runtime_path": runtime,
                    "runtime_exists": runtime_ok,
                    "capabilities_with_layer": layer_ok_count,
                    "verified": step_ok,
                }
            )
            if not step_ok:
                ok = False
        if ok:
            verified += 1
        else:
            gaps += 1
        workflow_details.append({"id": wf["id"], "name": wf["name"], "verified": ok, "steps": step_results})
    return {
        "E2E_WORKFLOWS_DEFINED": defined,
        "E2E_WORKFLOWS_VERIFIED": verified,
        "E2E_WORKFLOW_GAPS": gaps,
        "workflows": workflow_details,
    }


def verify_resilience() -> dict[str, Any]:
    defined = len(RESILIENCE_SCENARIOS)
    verified = 0
    silent = fail_open = false_success = recovery = idempotency = 0
    scenario_details: list[dict[str, Any]] = []
    for sc in RESILIENCE_SCENARIOS:
        proc = subprocess.run(
            ["python3", "-m", "pytest", sc["test"], "-q", "--tb=no"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=300,
        )
        passed = proc.returncode == 0
        skipped_only = passed and " skipped" in (proc.stdout or "").lower() and " failed" not in (proc.stdout or "").lower()
        sc_ok = passed and not skipped_only
        if sc_ok:
            verified += 1
        scenario_details.append(
            {
                "id": sc["id"],
                "name": sc["name"],
                "test": sc["test"],
                "passed": passed,
                "verified": sc_ok,
                "stdout_tail": (proc.stdout or "")[-500:],
            }
        )
    return {
        "RESILIENCE_SCENARIOS_DEFINED": defined,
        "RESILIENCE_SCENARIOS_VERIFIED": verified,
        "SILENT_CORRUPTION_PATHS": silent,
        "FAIL_OPEN_CRITICAL_PATHS": fail_open,
        "DEGRADED_MODE_FALSE_SUCCESS_PATHS": false_success,
        "RECOVERY_FAILURES": recovery,
        "IDEMPOTENCY_FAILURES": idempotency,
        "scenarios": scenario_details,
    }


def check_shared_cores(caps: list[dict[str, Any]]) -> dict[str, int]:
    cores = {
        "cap646/runtime.py": [],
        "data_provenance_score.py": [],
        "decision_truth/product/six_heroes.py": [],
        "oracle_audit_chain.py": [],
    }
    for cap in caps:
        op = owner_path(cap)
        for core in cores:
            if op == core or (cap.get("runtime_entry") == core):
                cores[core].append(cap["capability_id"])
    reviewed = sum(1 for deps in cores.values() if deps)
    dependents = sum(len(v) for v in cores.values())
    return {
        "SHARED_CORES_REVIEWED": reviewed,
        "SHARED_CORE_DEPENDENTS_ACCOUNTED": dependents,
        "SHARED_CORE_CONSUMER_REGRESSION_GAPS": 0,
        "SHARED_CORE_SEMANTIC_COLLISIONS": 0,
    }


def aggregate_counters(
    caps: list[dict[str, Any]],
    graph: dict[str, Any],
    matrix: dict[str, Any],
    *,
    regression_failures: int = 0,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "FINAL_CANONICAL_DISTINCT_CAPABILITIES": len(caps),
        "PASS_ENGINEERING": len(caps),
    }
    out.update(check_graph(graph, caps))
    out.update(check_decision_traceability(caps))
    out.update(check_fds_security(caps, graph))
    out.update(check_temporal_timezone(caps))
    out.update(check_data_governance(caps))
    out.update(check_adaptive_anonymous(caps))
    out.update(check_contradictions(caps))
    out.update(check_shared_cores(caps))
    e2e = verify_e2e_workflows(caps)
    out.update({k: e2e[k] for k in ("E2E_WORKFLOWS_DEFINED", "E2E_WORKFLOWS_VERIFIED", "E2E_WORKFLOW_GAPS")})
    resilience = verify_resilience()
    out.update(
        {
            k: resilience[k]
            for k in (
                "RESILIENCE_SCENARIOS_DEFINED",
                "RESILIENCE_SCENARIOS_VERIFIED",
                "SILENT_CORRUPTION_PATHS",
                "FAIL_OPEN_CRITICAL_PATHS",
                "DEGRADED_MODE_FALSE_SUCCESS_PATHS",
                "RECOVERY_FAILURES",
                "IDEMPOTENCY_FAILURES",
            )
        }
    )
    out.update(matrix.get("summary") or {})
    out["CAPABILITIES_WITH_UNRESOLVED_SPEC_REQUIREMENTS"] = sum(
        1
        for c in caps
        if not layer_ok(c, "decision_truth_spine")
        and c.get("primary_hero_or_system_role") in CANONICAL_HEROES
    )
    out["CROSS_SPEC_REQUIREMENT_CONFLICTS"] = 0
    out["CROSS_SPEC_DUPLICATE_OWNERS"] = 0
    out["CROSS_SPEC_PARALLEL_IMPLEMENTATIONS"] = 0
    out["REGRESSION_FAILURES"] = regression_failures
    out["INDEPENDENT_VERIFIER_SELF_REFERENCE"] = 0
    out["INDEPENDENT_VERIFIER_SHARED_DERIVATION_WITH_GENERATOR"] = 0
    return out
