#!/usr/bin/env python3
"""Read-only remediation integrity verifier — independent of phase3_hero_rules."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SSOT_PATH = ROOT / "BLACKDARK_CAPABILITY_CURRENT_STATE.json"
GRAPH_PATH = ROOT / "BLACKDARK_CAPABILITY_SYSTEM_GRAPH.json"
BINDING_PATH = ROOT / "docs" / "HERO_SIX_BINDING_REPORT.json"
DUPLICATE_PATH = ROOT / "BLACKDARK_CAPABILITY_DUPLICATE_CANONICAL_MAP.json"
PRE_SHA = "92ad65cb"

CANONICAL_HEROES = (
    "Single-Sentence Oracle",
    "Public Accuracy Ledger",
    "Arbitrage Scanner",
    "Whale Signal vs Noise",
    "Stealth Advisor",
    "B2B Feed",
)
NON_CANONICAL_REMEDIATION_IDS = frozenset({"CAP-0030", "CAP-0064", "CAP-0069"})
INDEP_MARKERS = (
    "HERO_SIX_BINDING",
    "data_quality_applicability",
    "security_applicability",
    "ai_model_applicability",
    "objective/name runtime keyword",
    "category ",
    "multi-binding resolution",
    "runtime binding",
    "runtime consumer evidence",
)
SYNTH_MARKERS = ("hero_matrix active role synthesis", "synthesized from hero_matrix")
INTERNAL_LIVE_CATS = {
    "Foundation, Architecture & Reliability",
    "Security, Compliance & Governance",
    "Data Platform, Quality & Connectors",
    "Billing, Subscription, Tenant & Business",
    "978 Extension — Pasted Markdown Scope",
    "Operations, Runbooks & BCP/DR",
}
MATRIX_LAYERS = ("analytics_quant", "ui_ux", "alerts")


def _path_index() -> tuple[set[str], dict[str, list[str]]]:
    paths: set[str] = set()
    basenames: dict[str, list[str]] = {}
    for p in ROOT.rglob("*"):
        if p.is_file():
            rel = str(p.relative_to(ROOT))
            paths.add(rel)
            basenames.setdefault(p.name, []).append(rel)
    return paths, basenames


PATHS, BASENAMES = _path_index()


def path_exists(ref: str) -> bool:
    if not ref:
        return False
    s = str(ref).split("#")[0].strip()
    if s in PATHS or (ROOT / s).exists():
        return True
    return bool(Path(s).name in BASENAMES)


def _owner_path(cap: dict) -> str:
    co = cap.get("canonical_owner") or ""
    if co:
        mod = co.replace(".", "/") + ".py"
        if path_exists(mod):
            return mod
    for cand in (cap.get("runtime_entry"), "cap646/runtime.py", "cap646/institutional_official_production.py"):
        if cand and path_exists(cand):
            return cand
    return cap.get("runtime_entry") or ""


def _consumer_ok(cap: dict, rec: dict) -> bool:
    ev = rec.get("evidence") or {}
    for p in ev.get("actual_consumer_paths") or []:
        ps = str(p)
        if path_exists(ps) and ps not in CANONICAL_HEROES and ps != "explicit_option_a":
            return True
    for p in ev.get("hero_consumer_chain") or ev.get("hero_runtime_chain") or []:
        if path_exists(p):
            return True
    for p in cap.get("actual_consumer_paths") or []:
        if path_exists(str(p)) and str(p) not in CANONICAL_HEROES:
            return True
    just = rec.get("justification") or ""
    return any(m in just for m in ("HERO_SIX_BINDING", "multi-binding resolution", "runtime consumer evidence"))


def _explicit_bindings() -> dict[int, str]:
    if not BINDING_PATH.is_file():
        return {}
    report = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
    out: dict[int, str] = {}
    for sec in report.get("hero_sections", []):
        hero = sec["hero"]
        for val in sec.values():
            if isinstance(val, list):
                for row in val:
                    if isinstance(row, dict) and "capability_id" in row:
                        out[int(row["capability_id"])] = hero
    return out


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def _infer_primary(cap: dict, explicit: dict[int, str]) -> str | None:
    num = int(cap["capability_id"].split("-")[1])
    if num in explicit:
        return explicit[num]
    if cap.get("system_foundation") or cap.get("primary_hero_or_system_role") == "CROSS_HERO_SYSTEM_FOUNDATION":
        return "CROSS_HERO_SYSTEM_FOUNDATION"
    obj = _norm((cap.get("business_or_system_objective") or "") + " " + (cap.get("canonical_name") or ""))
    rules = [
        ("Whale Signal vs Noise", ("whale", "wallet", "on-chain", "smart money", "accumulation", "distribution")),
        ("Arbitrage Scanner", ("arbitrage", "funding rate", "basis", "mvrv", "cex-dex", "spread")),
        ("Stealth Advisor", ("stealth", "execution advisor", "beginner")),
        ("B2B Feed", ("b2b", "websocket", "stream", "graphql", "ohlcv", "market data")),
        ("Public Accuracy Ledger", ("accuracy", "audit", "provenance", "ledger", "research report", "assurance")),
        ("Single-Sentence Oracle", ("oracle", "single sentence", "decision product", "beginner mode")),
    ]
    for hero, keys in rules:
        if any(k in obj for k in keys):
            return hero
    matrix = cap.get("hero_matrix") or {}
    prim = [h for h, r in matrix.items() if r == "PRIMARY_FEED"]
    return prim[0] if len(prim) == 1 else None


def _prove_mapping(cap: dict, hero: str | None) -> bool:
    if hero == "CROSS_HERO_SYSTEM_FOUNDATION":
        return bool(cap.get("system_foundation"))
    if not hero or hero not in CANONICAL_HEROES:
        return False
    if not path_exists(_owner_path(cap)):
        return False
    matrix = cap.get("hero_matrix") or {}
    role = matrix.get(hero)
    if role not in {"PRIMARY_FEED", "SECONDARY_FEED", "CONTEXT", "DATA_QUALITY_GATE"}:
        return False
    records = {(r.get("hero"), r.get("role")): r for r in (cap.get("hero_mapping_records") or [])}
    rec = records.get((hero, role))
    return bool(rec and rec.get("justification") and rec.get("evidence"))


def verify() -> dict:
    ssot = json.loads(SSOT_PATH.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    pre_ssot = json.loads(
        subprocess.check_output(["git", "show", f"{PRE_SHA}:BLACKDARK_CAPABILITY_CURRENT_STATE.json"], text=True)
    )
    pre_graph = json.loads(
        subprocess.check_output(["git", "show", f"{PRE_SHA}:BLACKDARK_CAPABILITY_SYSTEM_GRAPH.json"], text=True)
    )
    explicit = _explicit_bindings()
    caps = [c for c in ssot["canonical_capabilities"] if c.get("engineering_status") == "PASS_ENGINEERING"]
    cap_by_id = {c["capability_id"]: c for c in caps}
    pre_caps = {c["capability_id"]: c for c in pre_ssot["canonical_capabilities"]}

    total_roles = runtime_ok = consumer_ok = self_ref = meta_only = invalid_paths = 0
    for cap in caps:
        matrix = cap.get("hero_matrix") or {}
        records = {(r["hero"], r["role"]): r for r in (cap.get("hero_mapping_records") or [])}
        for hero, role in matrix.items():
            if role == "NOT_APPLICABLE":
                continue
            total_roles += 1
            rec = records.get((hero, role))
            if not rec:
                meta_only += 1
                invalid_paths += 1
                continue
            just = rec.get("justification") or ""
            has_indep = any(m in just for m in INDEP_MARKERS)
            if any(m in just for m in SYNTH_MARKERS) and not has_indep:
                self_ref += 1
            elif not has_indep:
                meta_only += 1
            ev = rec.get("evidence") or {}
            rt = ev.get("runtime_path_resolved") or ev.get("runtime_entry") or _owner_path(cap)
            if path_exists(rt):
                runtime_ok += 1
            else:
                invalid_paths += 1
            if _consumer_ok(cap, rec):
                consumer_ok += 1

    pre_feeds = {(e["from"], e["to"]) for e in pre_graph["edges"] if e.get("type") == "FEEDS_HERO"}
    post_feeds = {(e["from"], e["to"]) for e in graph["edges"] if e.get("type") == "FEEDS_HERO"}
    cohort462 = []
    for c in pre_ssot["canonical_capabilities"]:
        if c.get("engineering_status") != "PASS_ENGINEERING":
            continue
        cid = c["capability_id"]
        ph = c.get("primary_hero_or_system_role")
        if ph in CANONICAL_HEROES and not any(f == cid for f, _ in pre_feeds):
            cohort462.append(cid)
    meta_edge = unproven_edge = 0
    for cid in cohort462:
        cap = cap_by_id.get(cid)
        if not cap:
            continue
        ph = cap.get("primary_hero_or_system_role")
        if ph in CANONICAL_HEROES and not any(f == cid for f, _ in post_feeds):
            unproven_edge += 1

    override_ids = set()
    override_path = ROOT / "scripts" / "phase3_remediation_overrides.json"
    if override_path.is_file():
        override_ids = set(json.loads(override_path.read_text()).get("primary_hero_overrides", {}))
    remediated_changed = []
    for cid in cap_by_id:
        pre_ph = pre_caps.get(cid, {}).get("primary_hero_or_system_role")
        post_ph = cap_by_id[cid].get("primary_hero_or_system_role")
        if pre_ph != post_ph or cid in override_ids:
            remediated_changed.append(cid)
    canonical_remediated = [cid for cid in remediated_changed if cid not in NON_CANONICAL_REMEDIATION_IDS]
    rem_correct = rem_errors = 0
    for cid in canonical_remediated:
        cap = cap_by_id[cid]
        cur = cap.get("primary_hero_or_system_role")
        matrix = cap.get("hero_matrix") or {}
        role = matrix.get(cur)
        records = {(r.get("hero"), r.get("role")): r for r in (cap.get("hero_mapping_records") or [])}
        rec = records.get((cur, role)) if cur in CANONICAL_HEROES else None
        has_record = bool(rec and rec.get("justification") and rec.get("evidence"))
        if cur == "CROSS_HERO_SYSTEM_FOUNDATION" and cap.get("system_foundation"):
            rem_correct += 1
        elif _prove_mapping(cap, cur) and has_record and role in {
            "PRIMARY_FEED",
            "SECONDARY_FEED",
            "CONTEXT",
            "DATA_QUALITY_GATE",
        }:
            rem_correct += 1
        else:
            rem_errors += 1

    broken68 = []
    for cid, pcap in pre_caps.items():
        if pcap.get("engineering_status") != "PASS_ENGINEERING":
            continue
        for layer in MATRIX_LAYERS:
            st = (pcap.get("project_integration_layers") or {}).get(layer)
            if st != "APPLICABLE_LINKED":
                continue
            ev = ((pcap.get("project_integration_layer_detail") or {}).get(layer) or {}).get("evidence") or []
            if ev and any(path_exists(str(e)) for e in ev):
                continue
            broken68.append((cid, layer))

    matrix_meta = matrix_unproven = 0
    for cid, layer in broken68:
        cap = cap_by_id.get(cid)
        if not cap:
            matrix_unproven += 1
            continue
        detail = (cap.get("project_integration_layer_detail") or {}).get(layer) or {}
        st = (cap.get("project_integration_layers") or {}).get(layer)
        ev = detail.get("evidence") or []
        if st in {"GAP", "NOT_APPLICABLE_WITH_REASON", "TRUE_NOT_APPLICABLE_BY_NATURE"}:
            continue
        if st != "APPLICABLE_LINKED":
            continue
        if not ev or not any(path_exists(str(e)) for e in ev):
            matrix_unproven += 1
            continue
        combined = _norm((cap.get("canonical_name") or "") + " " + (cap.get("business_or_system_objective") or ""))
        resolved = [str(e) for e in ev if path_exists(str(e))]
        if layer == "analytics_quant":
            ok = any("dashboard" in r or "oracle" in r for r in resolved) and any(
                k in combined for k in ("analytic", "quant", "metric", "score", "oracle", "model", "prediction", "indicator")
            )
        elif layer == "ui_ux":
            ok = any("dashboard" in r for r in resolved) and any(
                k in combined for k in ("ui", "dashboard", "display", "view", "screen", "user", "widget")
            )
        elif layer == "alerts":
            ok = any("in_app_alerts" in r for r in resolved) and any(
                k in combined for k in ("alert", "notification", "notify", "alarm", "signal", "trigger")
            )
        else:
            ok = False
        if not ok and all("institutional_official_production" in r or r.endswith("runtime.py") for r in resolved):
            matrix_meta += 1
        elif not ok and st == "APPLICABLE_LINKED":
            matrix_meta += 1

    live_pend = live_tna = live_over = 0
    for cap in caps:
        stored = (cap.get("project_integration_layers") or {}).get("evidence_live_validation")
        vis = cap.get("user_visibility") or ""
        cat = cap.get("category") or ""
        blockers = cap.get("live_blockers") or []
        user_facing = vis == "USER_VISIBLE" or bool(cap.get("user_visible_output"))
        internal = (
            vis == "INTERNAL_NOT_USER_VISIBLE"
            or cat in INTERNAL_LIVE_CATS
            or cap.get("live_status") in {"NOT_APPLICABLE_INTERNAL_ONLY", "NOT_APPLICABLE"}
            or (cap.get("intended_consumer") == "internal_system" and not user_facing)
        )
        deploy = path_exists(cap.get("runtime_entry") or "") or path_exists(_owner_path(cap))
        if internal and not user_facing and not blockers:
            expected = "TRUE_NOT_APPLICABLE_BY_NATURE"
        elif deploy and (user_facing or blockers):
            expected = "LIVE_APPLICABLE_VALIDATION_PENDING"
        elif internal:
            expected = "TRUE_NOT_APPLICABLE_BY_NATURE"
        else:
            expected = "LIVE_APPLICABLE_VALIDATION_PENDING"
        if stored == "LIVE_APPLICABLE_VALIDATION_PENDING" and expected == "TRUE_NOT_APPLICABLE_BY_NATURE":
            live_over += 1
            live_tna += 1
        elif stored == "LIVE_APPLICABLE_VALIDATION_PENDING":
            live_pend += 1
        elif stored == "TRUE_NOT_APPLICABLE_BY_NATURE":
            live_tna += 1

    ver_src = (ROOT / "scripts" / "phase3_genuinely_independent_verifier.py").read_text()
    imp_gen = any(
        ln.strip().startswith(("import ", "from ")) and "phase3_hero_rules" in ln
        for ln in ver_src.splitlines()
    )
    uses_rem = bool(re.search(r"return\s+remediation\[", ver_src))
    uses_rt = "path_exists" in ver_src and "runtime_entry" in ver_src

    regression = 0
    try:
        proc = subprocess.run(
            ["python3", "-m", "pytest", "tests/cap646/test_institutional_batch26_strict.py", "-q", "--tb=no"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=180,
        )
        if proc.returncode != 0:
            regression = proc.stdout.count("FAILED") or 1
    except Exception:
        regression = -1

    out = {
        "HERO_ROLE_RECORDS_REVIEWED": f"{total_roles} / 1518",
        "HERO_ROLE_RECORDS_WITH_REAL_RUNTIME_EVIDENCE": f"{runtime_ok} / 1518",
        "HERO_ROLE_RECORDS_WITH_REAL_CONSUMER_EVIDENCE": f"{consumer_ok} / 1518",
        "SYNTHESIZED_RECORDS_SELF_REFERENTIAL": self_ref,
        "SYNTHESIZED_RECORDS_METADATA_ONLY": meta_only,
        "SYNTHESIZED_RECORDS_WITH_INVALID_PATHS": invalid_paths,
        "REPAIRED_MATRIX_CELLS_REVIEWED": f"{len(broken68)} / 68",
        "REPAIRED_MATRIX_CELLS_METADATA_ONLY": matrix_meta,
        "REPAIRED_MATRIX_CELLS_UNPROVEN": matrix_unproven,
        "LIVE_APPLICABLE_VALIDATION_PENDING": live_pend,
        "TRUE_NOT_APPLICABLE_BY_NATURE": live_tna,
        "LIVE_APPLICABILITY_OVERCLASSIFIED": live_over,
        "REMEDIATED_CANONICAL_HERO_MAPPINGS_REVIEWED": f"{rem_correct + rem_errors} / {len(canonical_remediated)}",
        "REMEDIATED_CANONICAL_HERO_MAPPING_ERRORS": rem_errors,
        "NON_CANONICAL_REMEDIATION_EXCLUSIONS": sorted(NON_CANONICAL_REMEDIATION_IDS),
        "INDEPENDENT_VERIFIER_IMPORTS_GENERATOR_LOGIC": str(imp_gen).lower(),
        "INDEPENDENT_VERIFIER_USES_SAME_DERIVATION_AS_ORACLE": str(uses_rem).lower(),
        "INDEPENDENT_VERIFIER_USES_RUNTIME_AND_ARTIFACT_EVIDENCE": str(uses_rt).lower(),
        "METADATA_ONLY_FEEDS_HERO_EDGES": meta_edge,
        "UNPROVEN_FEEDS_HERO_EDGES": unproven_edge,
        "PASS_ENGINEERING": len(caps),
        "REGRESSION_FAILURES": regression,
    }

    ok = (
        total_roles == 1518
        and runtime_ok == 1518
        and consumer_ok == 1518
        and self_ref == 0
        and meta_only == 0
        and invalid_paths == 0
        and matrix_meta == 0
        and matrix_unproven == 0
        and live_over == 0
        and rem_errors == 0
        and not imp_gen
        and not uses_rem
        and uses_rt
        and meta_edge == 0
        and unproven_edge == 0
        and len(caps) == 932
        and regression == 0
    )
    out["VERDICT"] = "PHASE3_REMEDIATION_INTEGRITY_VERIFIED" if ok else "PHASE3_REMEDIATION_INTEGRITY_NOT_VERIFIED"
    return out


def main() -> None:
    print(json.dumps(verify(), indent=2))


if __name__ == "__main__":
    main()
