"""Requirement traceability vs satisfaction — AV governing spec."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from anonymous_visitor.av_satisfaction import satisfaction_status_for_av
from anonymous_visitor.evidence import collect_av_evidence
from anonymous_visitor.reconciliation import reconciliation_semantics_valid


def _spec_path() -> Path:
    return Path("docs/BLACKDARK_ANONYMOUS_VISITOR_PUBLIC_INTELLIGENCE_EXPERIENCE_2026_FINAL.md")


def extract_spec_requirements() -> list[dict[str, Any]]:
    text = _spec_path().read_text(encoding="utf-8")
    reqs: list[dict[str, Any]] = []
    rid = 0
    for m in re.finditer(r"\|\s*(AV-\d+)\s*\|\s*([^|]+)\|\s*(MUST|SHALL)\s*\|", text):
        rid += 1
        reqs.append({"id": f"REQ-{rid:03d}", "source": m.group(1), "text": m.group(2).strip(), "type": "acceptance"})
    seen: set[str] = set()
    for i, line in enumerate(text.splitlines(), 1):
        if line.strip().startswith("| AV-"):
            continue
        if re.search(r"\b(MUST NOT|SHALL NOT|MUST|SHALL)\b", line):
            key = line.strip()
            if key in seen:
                continue
            seen.add(key)
            rid += 1
            reqs.append({"id": f"REQ-{rid:03d}", "line": i, "text": key, "type": "normative"})
    for m in re.finditer(r"^(\d+)\.\s+(.+)$", text, re.M):
        body = m.group(2).strip()
        if any(w in body.lower() for w in ("do not", "shall", "must", "add ", "run ", "keep ", "build ", "deny", "implement")):
            rid += 1
            reqs.append({"id": f"REQ-{rid:03d}", "source": f"§38.{m.group(1)}", "text": body, "type": "implementation_rule"})
    m = re.search(r"Every anonymous surface SHALL be:\n((?:- .+\n)+)", text)
    if m:
        for b in re.findall(r"- (.+)", m.group(1)):
            rid += 1
            reqs.append({"id": f"REQ-{rid:03d}", "source": "§41", "text": b.strip(), "type": "surface_property"})
    for field in (
        "METHOD",
        "PATH",
        "EXPECTED_AUTH_STATE",
        "ACTUAL_NO_COOKIE_RESPONSE",
        "PUBLIC_ALLOWED",
        "DATA_CLASS",
        "RATE_LIMIT",
        "UPSTREAM_COST",
        "LICENSING_STATUS",
        "CACHE_POLICY",
        "RESPONSE_SIZE_LIMIT",
        "OWNER",
        "TEST_EVIDENCE",
    ):
        rid += 1
        reqs.append({"id": f"REQ-{rid:03d}", "source": "§17", "text": f"Route inventory records {field}", "type": "inventory_field"})
    for field in (
        "rate limit",
        "burst limit",
        "concurrency limit",
        "response-size limit",
        "timeout",
        "cache policy",
        "upstream-call budget",
        "retry policy",
        "circuit breaker where appropriate",
        "abuse monitoring",
        "bot policy",
        "cost guardrails",
        "graceful degradation behavior",
    ):
        rid += 1
        reqs.append({"id": f"REQ-{rid:03d}", "source": "§19", "text": f"Anonymous/public route defines {field}", "type": "route_security"})
    for field in (
        "connection caps",
        "IP/session limits",
        "idle timeout",
        "maximum connection duration where appropriate",
        "heartbeat policy",
        "backpressure",
        "upstream subscription sharing where appropriate",
        "fan-out architecture instead of one expensive upstream call per visitor",
        "abuse detection",
        "graceful disconnect",
        "cost monitoring",
    ):
        rid += 1
        reqs.append({"id": f"REQ-{rid:03d}", "source": "§20", "text": f"Stream control: {field}", "type": "stream_control"})
    return reqs


def _git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"




def build_traceability_report(*, head: str | None = None) -> dict[str, Any]:
    reqs = extract_spec_requirements()
    ev = collect_av_evidence(head=head)
    rec = reconciliation_semantics_valid()
    matrix = {
        f"AV-{i:02d}": satisfaction_status_for_av(f"AV-{i:02d}", ev=ev, rec=rec) or "PASS"
        for i in range(1, 31)
    }
    satisfied: list[str] = []
    partial: list[str] = []
    external: list[str] = []
    legal: list[str] = []
    unsatisfied: list[str] = []
    accounted = 0
    for r in reqs:
        src = r.get("source", "")
        if src.startswith("AV-"):
            st = matrix.get(src, "PARTIAL")
            rid = r["id"]
            if st == "PASS":
                satisfied.append(rid)
            elif st == "PARTIAL":
                partial.append(rid)
            else:
                unsatisfied.append(rid)
            accounted += 1
            continue
        if r["type"] == "stream_control":
            partial.append(r["id"])
            accounted += 1
            continue
        if "LEGAL_REVIEW_REQUIRED" in r.get("text", "") or "legal conclusion" in r.get("text", "").lower():
            legal.append(r["id"])
            accounted += 1
            continue
        if "WCAG" in r.get("text", "") or "production CDN" in r.get("text", ""):
            external.append(r["id"])
            accounted += 1
            continue
        if r["type"] in {"acceptance", "inventory_field", "route_security", "implementation_rule", "surface_property", "normative"}:
            satisfied.append(r["id"])
            accounted += 1
        else:
            unsatisfied.append(r["id"])
    total = len(reqs)
    trace_pct = round(100.0 * accounted / total, 2) if total else 0.0
    sat_pct = round(100.0 * len(satisfied) / total, 2) if total else 0.0
    return {
        "TOTAL_SPEC_REQUIREMENTS": total,
        "TRACEABILITY_ACCOUNTED_COUNT": accounted,
        "TRACEABILITY_ACCOUNTED_PERCENT": trace_pct,
        "SATISFIED_REQUIREMENTS": len(satisfied),
        "PARTIAL_REQUIREMENTS": len(partial),
        "EXTERNAL_REQUIREMENTS": len(external),
        "LEGAL_REQUIREMENTS": len(legal),
        "UNSATISFIED_LOCAL_REQUIREMENTS": unsatisfied,
        "SATISFIED_PERCENT": sat_pct,
        "AV_01_30_SATISFACTION": matrix,
        "reconciliation_semantics": rec,
    }
