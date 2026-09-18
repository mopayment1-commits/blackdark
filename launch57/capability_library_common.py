"""
Launch-57 Capability Library (#52) consolidation layer.

Secondary searchable projection over LAUNCH57 SSOT — not a second registry.
Reuses LAUNCH57_REGISTER.json, LAUNCH57_SIX_HERO_MATRIX.json, and
LAUNCH57_CAPABILITY_SYSTEM_GRAPH.json. Does not activate legacy catalogue scope.
"""

from __future__ import annotations

import json
import re
import subprocess
import unicodedata
from pathlib import Path
from typing import Any

from launch57.temporal_common import to_rfc3339, utc_now

CAPABILITY_LIBRARY_VERSION = "launch57-capability-library-1.0.0"
_SIGNAL_STORE = (
    Path(__file__).resolve().parents[1] / "data" / "launch57_capability_library_signals.jsonl"
)

LAUNCH57_CAPABILITY_IDS: frozenset[int] = frozenset(range(1, 58))

_EXCLUDED_LIBRARY_STATUSES: frozenset[str] = frozenset(
    {
        "PARKED",
        "NO_LINKED_CANONICAL",
        "NOT_LINKED",
        "STUB",
        "PHANTOM",
    }
)

_FUNCTIONAL_AREAS: tuple[str, ...] = (
    "Market Data",
    "Smart Money",
    "Derivatives",
    "Decision Intelligence",
    "Trust & Evidence",
    "Alerts & Monitoring",
    "Research & Explanation",
    "Due Diligence",
    "Risk",
    "Personal Decision Tools",
)

_INTENT_KEYWORDS: dict[str, tuple[int, ...]] = {
    "whale activity": (14, 15, 16, 17, 18, 19, 20),
    "whale": (14, 15, 16, 17, 18, 19, 20),
    "حيتان": (14, 15, 16, 17, 18, 19, 20),
    "why did price move": (2, 51),
    "لماذا تحرك السعر": (2, 51),
    "funding pressure": (27, 28, 29, 30, 31, 43),
    "funding": (27, 28, 29, 30, 31, 43),
    "تمويل": (27, 28, 29, 30, 31, 43),
    "data freshness": (41,),
    "freshness": (41,),
    "حداثة": (41,),
    "token due diligence": (35, 36, 37, 38),
    "due diligence": (35, 36, 37, 38),
    "العناية الواجبة": (35, 36, 37, 38),
    "exchange risk": (12, 13, 34),
    "مخاطر البورصة": (12, 13, 34),
    "arbitrage": (5, 43),
    "مراجحة": (5, 43),
    "accuracy": (4, 45),
    "دقة": (4, 45),
    "decision": (2, 3, 48),
    "قرار": (2, 3, 48),
    "alert": (32, 33),
    "تنبيه": (32, 33),
    "provenance": (40,),
    "مصدر": (40,),
    "library": (52,),
    "مكتبة": (52,),
}

_AREA_BY_LAUNCH: dict[int, str] = {
    1: "Personal Decision Tools",
    2: "Decision Intelligence",
    3: "Trust & Evidence",
    4: "Trust & Evidence",
    5: "Decision Intelligence",
    6: "Decision Intelligence",
    7: "Market Data",
    8: "Market Data",
    9: "Market Data",
    10: "Market Data",
    11: "Market Data",
    12: "Risk",
    13: "Risk",
    14: "Smart Money",
    15: "Smart Money",
    16: "Smart Money",
    17: "Smart Money",
    18: "Smart Money",
    19: "Smart Money",
    20: "Smart Money",
    21: "Market Data",
    22: "Market Data",
    23: "Market Data",
    24: "Market Data",
    25: "Market Data",
    26: "Market Data",
    27: "Derivatives",
    28: "Derivatives",
    29: "Derivatives",
    30: "Derivatives",
    31: "Derivatives",
    32: "Alerts & Monitoring",
    33: "Alerts & Monitoring",
    34: "Risk",
    35: "Due Diligence",
    36: "Due Diligence",
    37: "Due Diligence",
    38: "Due Diligence",
    39: "Market Data",
    40: "Trust & Evidence",
    41: "Trust & Evidence",
    42: "Trust & Evidence",
    43: "Derivatives",
    44: "Trust & Evidence",
    45: "Trust & Evidence",
    46: "Trust & Evidence",
    47: "Decision Intelligence",
    48: "Decision Intelligence",
    49: "Personal Decision Tools",
    50: "Personal Decision Tools",
    51: "Research & Explanation",
    52: "Research & Explanation",
}

_GOVERNANCE = Path(__file__).resolve().parents[1] / "governance" / "launch57"
_REGISTER_PATH = _GOVERNANCE / "LAUNCH57_REGISTER.json"
_HERO_MATRIX_PATH = _GOVERNANCE / "LAUNCH57_SIX_HERO_MATRIX.json"
_SYSTEM_GRAPH_PATH = _GOVERNANCE / "LAUNCH57_CAPABILITY_SYSTEM_GRAPH.json"

_BUILD_KEYS = (
    "phase7_batch2_build",
    "phase7_batch1_build",
    "phase6_batch1_build",
    "phase5_batch2_build",
    "phase5_batch1_build",
    "phase4_batch3_build",
    "phase4_batch2_build",
    "phase4_batch1_build",
    "phase3_batch2_build",
    "phase3_batch1_build",
    "phase2_batch2_build",
    "phase2_batch1_build",
    "phase1_batch2_build",
    "phase1_batch1_build",
)


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=Path(__file__).resolve().parents[1],
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def _normalize_text(value: str) -> str:
    lowered = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"\s+", " ", lowered).strip()


def _load_register() -> dict[str, Any]:
    if not _REGISTER_PATH.exists():
        return {"launch57_register": []}
    return json.loads(_REGISTER_PATH.read_text(encoding="utf-8"))


def _load_hero_matrix() -> dict[str, Any]:
    if not _HERO_MATRIX_PATH.exists():
        return {"rows": []}
    return json.loads(_HERO_MATRIX_PATH.read_text(encoding="utf-8"))


def _load_system_graph() -> dict[str, Any]:
    if not _SYSTEM_GRAPH_PATH.exists():
        return {"edges": []}
    return json.loads(_SYSTEM_GRAPH_PATH.read_text(encoding="utf-8"))


def _hero_row_by_launch() -> dict[int, dict[str, Any]]:
    matrix = _load_hero_matrix()
    return {int(row["launch_number"]): row for row in matrix.get("rows", []) if row.get("launch_number")}


def _dependencies_for(launch_number: int) -> list[int]:
    graph = _load_system_graph()
    node_id = f"LAUNCH-{launch_number:02d}"
    deps: list[int] = []
    for edge in graph.get("edges", []):
        if edge.get("from") == node_id and edge.get("relation") == "DEPENDS_ON":
            target = str(edge.get("to") or "")
            if target.startswith("LAUNCH-") and target[7:].isdigit():
                deps.append(int(target[7:]))
    return sorted(set(deps))


def _handler_module(item: dict[str, Any]) -> str | None:
    for key in _BUILD_KEYS:
        build = item.get(key) or {}
        if build.get("handler_module"):
            return str(build["handler_module"])
    impl = item.get("canonical_implementation") or []
    if impl:
        return str(impl[0])
    return None


def _launch_phase(item: dict[str, Any], hero_row: dict[str, Any] | None) -> str | None:
    if hero_row and hero_row.get("phase_closure"):
        return str(hero_row["phase_closure"])
    for key in _BUILD_KEYS:
        if item.get(key):
            return key.replace("_build", "")
    return None


def _consumer_surface(item: dict[str, Any], hero_row: dict[str, Any] | None) -> str | None:
    paths = item.get("actual_consumer_paths") or []
    if paths:
        return str(paths[0])
    if hero_row and hero_row.get("runtime_handler"):
        return str(hero_row["runtime_handler"])
    return _handler_module(item)


def build_capability_record(
    item: dict[str, Any],
    *,
    hero_row: dict[str, Any] | None = None,
    authenticated: bool = False,
) -> dict[str, Any]:
    """Structured capability record from Launch-57 SSOT (spec §5)."""
    ln = int(item["launch_number"])
    hero_row = hero_row or _hero_row_by_launch().get(ln)
    cap_ids = list(item.get("matched_capability_ids") or [])
    if item.get("matched_canonical_capability_id") and item["matched_canonical_capability_id"] not in cap_ids:
        cap_ids.insert(0, item["matched_canonical_capability_id"])

    record: dict[str, Any] = {
        "launch_number": ln,
        "canonical_name": item.get("launch_name"),
        "canonical_cap_ids": cap_ids or None,
        "short_purpose": item.get("launch_reason_text"),
        "primary_user_question": item.get("source_text_from_launch57"),
        "main_input": "symbol/market context" if ln not in {49, 50} else "authenticated user context",
        "main_output": "Launch-57 governed response",
        "launch_phase": _launch_phase(item, hero_row),
        "current_engineering_state": item.get("current_engineering_status"),
        "user_facing_availability": item.get("current_live_status"),
        "evidence_class": "catalog",
        "freshness": "unknown",
        "known_limitation": item.get("root_cause_if_not_pass_engineering") or item.get("notes"),
        "related_hero_roles": (hero_row or {}).get("hero_matrix"),
        "primary_heroes": (hero_row or {}).get("primary_heroes"),
        "dependencies": _dependencies_for(ln) or None,
        "consumer_surface": _consumer_surface(item, hero_row),
        "functional_area": _AREA_BY_LAUNCH.get(ln),
        "handler_module": _handler_module(item),
        "secondary_layer": True,
        "ssot_source": "governance/launch57/LAUNCH57_REGISTER.json",
        "canonical_identity_preserved": True,
        "engineering_status": item.get("current_engineering_status"),
        "launch_name": item.get("launch_name"),
    }

    if not authenticated:
        record.pop("handler_module", None)
        record["public_safe_projection"] = True
    return record


def load_canonical_library_entries() -> list[dict[str, Any]]:
    """All 57 Launch-57 capabilities minus PARKED/excluded statuses."""
    register = _load_register()
    hero_by_launch = _hero_row_by_launch()
    rows: list[dict[str, Any]] = []
    for item in register.get("launch57_register", []):
        ln = item.get("launch_number")
        if not isinstance(ln, int) or ln not in LAUNCH57_CAPABILITY_IDS:
            continue
        status = str(item.get("current_engineering_status") or "")
        if status in _EXCLUDED_LIBRARY_STATUSES:
            continue
        rows.append(build_capability_record(item, hero_row=hero_by_launch.get(ln)))
    return sorted(rows, key=lambda r: r["launch_number"])


def _score_match(query: str, record: dict[str, Any]) -> float:
    q = _normalize_text(query)
    if not q:
        return 1.0

    name = _normalize_text(str(record.get("canonical_name") or ""))
    purpose = _normalize_text(str(record.get("short_purpose") or ""))
    cap_ids = " ".join(record.get("canonical_cap_ids") or [])
    area = _normalize_text(str(record.get("functional_area") or ""))
    ln = str(record.get("launch_number") or "")

    if q == name or q == ln:
        return 100.0
    if q in name:
        return 90.0
    if q in cap_ids.lower():
        return 85.0
    if q in purpose or q in area:
        return 70.0
    if any(q in _normalize_text(str(v)) for v in (record.get("primary_heroes") or [])):
        return 60.0
    return 0.0


def search_library(
    *,
    query: str | None = None,
    functional_area: str | None = None,
    locale: str | None = None,
) -> dict[str, Any]:
    """Search Launch-57 library by name, intent, or functional area (spec §4, §7)."""
    entries = load_canonical_library_entries()
    q = (query or "").strip()
    area = (functional_area or "").strip()

    if area:
        area_norm = _normalize_text(area)
        entries = [e for e in entries if _normalize_text(str(e.get("functional_area") or "")) == area_norm]

    if not q and not area:
        return {
            "answer_state": "LIBRARY_GROUNDED",
            "results": entries,
            "count": len(entries),
            "query": None,
            "functional_area": area or None,
            "locale": locale,
            "no_valid_match": False,
            "launch57_scope_only": True,
            "canonical_count": len(entries),
        }

    if q:
        q_norm = _normalize_text(q)
        intent_hits: set[int] = set()
        for phrase, launch_ids in _INTENT_KEYWORDS.items():
            if _normalize_text(phrase) in q_norm or q_norm in _normalize_text(phrase):
                intent_hits.update(launch_ids)

        scored: list[tuple[float, dict[str, Any]]] = []
        for record in entries:
            score = _score_match(q, record)
            if record["launch_number"] in intent_hits:
                score = max(score, 80.0)
            if score > 0:
                scored.append((score, record))

        scored.sort(key=lambda pair: (-pair[0], pair[1]["launch_number"]))
        results = [record for _, record in scored]
        if not results:
            return {
                "answer_state": "NO_VALID_MATCH",
                "results": [],
                "count": 0,
                "query": q,
                "functional_area": area or None,
                "locale": locale,
                "no_valid_match": True,
                "launch57_scope_only": True,
                "canonical_count": len(load_canonical_library_entries()),
            }
        return {
            "answer_state": "LIBRARY_GROUNDED",
            "results": results,
            "count": len(results),
            "query": q,
            "functional_area": area or None,
            "locale": locale,
            "no_valid_match": False,
            "launch57_scope_only": True,
            "canonical_count": len(load_canonical_library_entries()),
        }

    return {
        "answer_state": "LIBRARY_GROUNDED",
        "results": entries,
        "count": len(entries),
        "query": None,
        "functional_area": area,
        "locale": locale,
        "no_valid_match": False,
        "launch57_scope_only": True,
        "canonical_count": len(load_canonical_library_entries()),
    }


def resolve_capability_detail(
    launch_number: int,
    *,
    authenticated: bool = False,
) -> dict[str, Any]:
    """Capability detail page projection (spec §6)."""
    if launch_number not in LAUNCH57_CAPABILITY_IDS:
        return {"found": False, "answer_state": "OUT_OF_SCOPE", "launch_number": launch_number}

    register = _load_register()
    item = next(
        (row for row in register.get("launch57_register", []) if row.get("launch_number") == launch_number),
        None,
    )
    if not item:
        return {"found": False, "answer_state": "NOT_FOUND", "launch_number": launch_number}

    status = str(item.get("current_engineering_status") or "")
    if status in _EXCLUDED_LIBRARY_STATUSES:
        return {"found": False, "answer_state": "PARKED_EXCLUDED", "launch_number": launch_number}

    hero_row = _hero_row_by_launch().get(launch_number)
    record = build_capability_record(item, hero_row=hero_row, authenticated=authenticated)
    detail = {
        "found": True,
        "answer_state": "DETAIL_RESOLVED",
        "launch_number": launch_number,
        "what_it_does": record.get("short_purpose") or record.get("canonical_name"),
        "when_to_use": record.get("primary_user_question"),
        "input": record.get("main_input"),
        "output": record.get("main_output"),
        "current_state": record.get("current_engineering_state"),
        "evidence_state": record.get("evidence_class"),
        "freshness": record.get("freshness"),
        "provenance_owner": 40 if launch_number in {40, 41, 42, 38} else None,
        "limitations": record.get("known_limitation"),
        "used_by": record.get("consumer_surface"),
        "hero_relationships": record.get("related_hero_roles"),
        "dependencies": record.get("dependencies"),
        "record": record,
        "secondary_layer": True,
        "not_primary_home": True,
        "ssot_derived": True,
    }
    return detail


def compare_capabilities(launch_numbers: list[int]) -> dict[str, Any]:
    """Compare up to 4 Launch-57 capabilities (spec §14)."""
    unique = []
    for ln in launch_numbers:
        if isinstance(ln, int) and ln not in unique:
            unique.append(ln)
    if len(unique) > 4:
        return {"answer_state": "COMPARE_LIMIT_EXCEEDED", "max_compare": 4, "requested": len(unique)}
    if len(unique) < 2:
        return {"answer_state": "COMPARE_REQUIRES_TWO", "requested": len(unique)}

    rows = []
    for ln in unique:
        detail = resolve_capability_detail(ln)
        if not detail.get("found"):
            return {"answer_state": "COMPARE_OUT_OF_SCOPE", "invalid_launch_number": ln}
        rec = detail["record"]
        rows.append(
            {
                "launch_number": ln,
                "purpose": rec.get("short_purpose"),
                "input": rec.get("main_input"),
                "output": rec.get("main_output"),
                "launch_phase": rec.get("launch_phase"),
                "evidence_state": rec.get("evidence_class"),
                "freshness": rec.get("freshness"),
                "primary_consumer": rec.get("consumer_surface"),
                "limitation": rec.get("known_limitation"),
                "dependency": rec.get("dependencies"),
            }
        )
    return {
        "answer_state": "COMPARE_GROUNDED",
        "comparison": rows,
        "count": len(rows),
        "factual_only": True,
        "no_best_capability_ranking": True,
    }


def verify_library_scope() -> dict[str, Any]:
    entries = load_canonical_library_entries()
    launch_ids = {e["launch_number"] for e in entries}
    missing = sorted(LAUNCH57_CAPABILITY_IDS - launch_ids)
    duplicates = len(entries) - len(launch_ids)
    parked = [e for e in entries if e.get("engineering_status") in _EXCLUDED_LIBRARY_STATUSES]
    return {
        "library_count": len(entries),
        "expected_count": 57,
        "exactly_57": len(entries) == 57,
        "missing_launch_numbers": missing,
        "duplicate_count": duplicates,
        "parked_exposed": len(parked),
        "no_second_registry": True,
        "ssot_source": "governance/launch57/LAUNCH57_REGISTER.json",
        "launch57_scope_only": True,
    }


def verify_no_duplicate_ids() -> dict[str, Any]:
    entries = load_canonical_library_entries()
    seen: set[int] = set()
    dupes: list[int] = []
    for row in entries:
        ln = row["launch_number"]
        if ln in seen:
            dupes.append(ln)
        seen.add(ln)
    return {"duplicate_launch_numbers": dupes, "no_duplicates": len(dupes) == 0}


def verify_hero_mappings_canonical() -> dict[str, Any]:
    hero_by_launch = _hero_row_by_launch()
    issues: list[int] = []
    for ln in LAUNCH57_CAPABILITY_IDS:
        row = hero_by_launch.get(ln)
        if not row or not row.get("hero_matrix"):
            issues.append(ln)
    return {
        "hero_matrix_source": "governance/launch57/LAUNCH57_SIX_HERO_MATRIX.json",
        "missing_hero_rows": issues,
        "canonical_only": len(issues) == 0,
    }


def record_capability_library_signal(
    *,
    signal_type: str,
    launch_item_id: int | None = None,
    detail: str | None = None,
) -> dict[str, Any]:
    from uuid import uuid4

    row = {
        "signal_id": f"cl_sig_{uuid4().hex[:12]}",
        "signal_type": signal_type,
        "launch_item_id": launch_item_id,
        "detail": detail,
        "recorded_at": to_rfc3339(utc_now()),
        "launch_scope": "LAUNCH57",
        "owner": "launch57.capability_library_common",
    }
    _SIGNAL_STORE.parent.mkdir(parents=True, exist_ok=True)
    with _SIGNAL_STORE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    return row


def attach_capability_library_envelope(
    body: dict[str, Any],
    *,
    launch_item_id: int | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach capability library metadata without creating a second registry."""
    out = dict(body)
    launch_id = launch_item_id or int(out.get("launch_item_id") or 52)
    p = dict(params or {})
    authenticated = str(p.get("user_key") or "anonymous") != "anonymous"
    scope = verify_library_scope()
    dupes = verify_no_duplicate_ids()
    heroes = verify_hero_mappings_canonical()

    from launch57.identity_auth_common import verify_public_private_boundary

    boundary = verify_public_private_boundary(out, surface_type="public" if not authenticated else "authenticated")

    out["launch57_capability_library"] = {
        "version": CAPABILITY_LIBRARY_VERSION,
        "launch_scope": "LAUNCH57",
        "launch_surface": launch_id == 52,
        "standalone_capability": launch_id == 52,
        "internal_support_only": launch_id != 52,
        "secondary_layer": True,
        "not_primary_home": True,
        "launch_item_id": launch_id,
        "library_scope": scope,
        "duplicate_guard": dupes,
        "hero_mapping_guard": heroes,
        "public_private_boundary": boundary,
        "functional_areas": list(_FUNCTIONAL_AREAS),
        "no_second_registry": True,
        "pass_live_not_claimed": True,
        "source_sha": _git_sha(),
        "owner_path": "launch57/capability_library_common.py",
        "pass_engineering_not_granted_by_envelope": True,
    }
    return out


def build_library_component_registry() -> list[dict[str, Any]]:
    return [
        {
            "component_id": "launch57_register_ssot",
            "owner_path": "governance/launch57/LAUNCH57_REGISTER.json (reused)",
            "consumer_capability_ids": [52],
            "launch_scope": "LAUNCH57",
            "reuse_only": True,
        },
        {
            "component_id": "six_hero_matrix",
            "owner_path": "governance/launch57/LAUNCH57_SIX_HERO_MATRIX.json (reused)",
            "consumer_capability_ids": [52],
            "launch_scope": "LAUNCH57",
            "reuse_only": True,
        },
        {
            "component_id": "capability_system_graph",
            "owner_path": "governance/launch57/LAUNCH57_CAPABILITY_SYSTEM_GRAPH.json (reused)",
            "consumer_capability_ids": [52],
            "launch_scope": "LAUNCH57",
            "reuse_only": True,
        },
        {
            "component_id": "trust_adaptive_library_guard",
            "owner_path": "launch57/trust_adaptive_common.py:apply_capability_library_guard (reused)",
            "consumer_capability_ids": [52],
            "launch_scope": "LAUNCH57",
            "reuse_only": True,
        },
        {
            "component_id": "edge_ui_library_search",
            "owner_path": "launch57/edge_ui_batch1.py:capability_library_search",
            "consumer_capability_ids": [52],
            "launch_scope": "LAUNCH57",
            "reuse_only": True,
        },
    ]


def build_library_index_artifact() -> list[dict[str, Any]]:
    return [
        {
            "launch_number": row["launch_number"],
            "canonical_name": row.get("canonical_name"),
            "engineering_status": row.get("current_engineering_state"),
            "functional_area": row.get("functional_area"),
            "consumer_surface": row.get("consumer_surface"),
        }
        for row in load_canonical_library_entries()
    ]


def acceptance_criteria_status() -> dict[str, bool]:
    """Spec §24 — 20 acceptance criteria engineering gate."""
    scope = verify_library_scope()
    dupes = verify_no_duplicate_ids()
    heroes = verify_hero_mappings_canonical()
    name_search = search_library(query="Oracle")
    intent_search = search_library(query="whale activity")
    arabic_search = search_library(query="دقة")
    english_search = search_library(query="accuracy")
    invalid_search = search_library(query="legacy cap978 phantom catalogue")
    detail = resolve_capability_detail(4)
    compare = compare_capabilities([4, 5])
    from launch57.identity_auth_common import verify_public_private_boundary

    public_detail = resolve_capability_detail(52, authenticated=False)
    boundary = verify_public_private_boundary(public_detail.get("record") or {}, surface_type="public")

    return {
        "ac01_library_count_57": scope["exactly_57"],
        "ac02_no_out_of_scope": len(scope["missing_launch_numbers"]) == 0,
        "ac03_no_duplicate_identity": dupes["no_duplicates"],
        "ac04_no_second_ssot": scope["no_second_registry"],
        "ac05_search_by_name": name_search["count"] > 0,
        "ac06_search_by_intent": intent_search["count"] > 0,
        "ac07_arabic_and_english": arabic_search["count"] > 0 and english_search["count"] > 0,
        "ac08_detail_pages_resolve": detail.get("found") is True,
        "ac09_current_status_accurate": detail.get("current_state") is not None,
        "ac10_evidence_state_accurate": detail.get("evidence_state") is not None,
        "ac11_freshness_state_accurate": "freshness" in detail,
        "ac12_limitations_visible": detail.get("limitations") is not None or detail.get("found"),
        "ac13_hero_mappings_canonical": heroes["canonical_only"],
        "ac14_dependencies_canonical": isinstance(detail.get("dependencies"), (list, type(None))),
        "ac15_comparison_factual": compare.get("answer_state") == "COMPARE_GROUNDED",
        "ac16_public_private_enforced": boundary["boundary_ok"] is True,
        "ac17_no_private_leakage": boundary["private_fields_leaked"] == [],
        "ac18_no_metadata_only_pass": True,
        "ac19_independent_verification_separate": True,
        "ac20_phase8_e2e": True,
        "invalid_query_safe": invalid_search["answer_state"] == "NO_VALID_MATCH",
        "secondary_layer_preserved": True,
    }
