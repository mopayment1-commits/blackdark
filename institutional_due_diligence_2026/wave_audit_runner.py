#!/usr/bin/env python3
"""Institutional audit waves 2-22 + final reconciliation. Read-only analysis."""
from __future__ import annotations

import ast
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/workspace")
OUT = ROOT / "institutional_due_diligence_2026"
GENERATED = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
SKIP = {".git", ".venv", "__pycache__"}


def load_json(name: str) -> dict:
    p = OUT / name
    return json.loads(p.read_text()) if p.is_file() else {}


def save_json(name: str, data: dict) -> None:
    (OUT / name).write_text(json.dumps(data, indent=2), encoding="utf-8")


def iter_py():
    for p in ROOT.rglob("*.py"):
        if any(s in p.parts for s in SKIP):
            continue
        yield p


def grep_count(pattern: str, path: str = ".") -> int:
    r = subprocess.run(
        ["rg", "-c", pattern, path, "--glob", "!.venv/**", "--glob", "!.git/**"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    if r.returncode not in (0, 1):
        return 0
    return sum(int(line.split(":")[-1]) for line in r.stdout.splitlines() if ":" in line)


findings: list[dict] = []
evidence: list[dict] = []
ev_id = 9


def add_evidence(title: str, method: str, result: str, level: str = "L0") -> str:
    global ev_id
    eid = f"EVD-{ev_id:03d}"
    ev_id += 1
    evidence.append({
        "id": eid, "title": title, "method": method,
        "result": result, "level": level, "generated": GENERATED,
    })
    return eid


def add_finding(**kw) -> None:
    findings.append(kw)


# --- WAVE 2: Architecture ---
def wave2() -> dict:
    imports = Counter()
    imported_by = defaultdict(set)
    for p in iter_py():
        rel = str(p.relative_to(ROOT))
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports[alias.name.split(".")[0]] += 1
            elif isinstance(node, ast.ImportFrom) and node.module:
                mod = node.module.split(".")[0]
                imports[mod] += 1
                imported_by[mod].add(rel)

    dashboard_size = (ROOT / "dashboard.py").stat().st_size
    todo_count = grep_count(r"\b(TODO|FIXME|HACK|NotImplemented|pass\s+#)\b")
    stub_count = grep_count(r"\b(placeholder|stub|mock.*production|fake_)\b", ".")

    e1 = add_evidence("dashboard.py monolith size", "stat", f"{dashboard_size} bytes")
    e2 = add_evidence("TODO/FIXME/HACK count", "rg", str(todo_count))
    add_finding(
        fid="WF-004", wave=2, severity="P2", title="Monolithic dashboard.py architecture",
        desc=f"Primary app file is {dashboard_size//1024}KB with 225+ direct routes; high coupling risk.",
        evidence=[e1], status="NOT VERIFIED",
    )
    if todo_count > 0:
        add_finding(
            fid="WF-005", wave=2, severity="P2", title=f"Technical debt markers in code ({todo_count} hits)",
            desc="TODO/FIXME/HACK/NotImplemented patterns found repo-wide.",
            evidence=[e2], status="OBSERVED",
        )

    top_imports = imports.most_common(20)
    return {
        "top_import_roots": top_imports,
        "dashboard_py_bytes": dashboard_size,
        "todo_fixme_count": todo_count,
        "stub_placeholder_hits": stub_count,
        "circular_dependency_scan": "NOT VERIFIED",
        "reachability": "NOT VERIFIED — requires runtime trace Wave 2",
    }


# --- WAVE 3: Models ---
def wave3() -> dict:
    model_files = []
    for p in iter_py():
        rel = str(p.relative_to(ROOT))
        txt = p.read_text(encoding="utf-8", errors="ignore").lower()
        if any(k in rel for k in ["oracle", "ml/", "regime", "sentiment", "alpha", "arbitrage", "predict"]):
            model_files.append(rel)
        elif any(k in txt[:3000] for k in ["def predict", "class.*model", "backtest", "confidence"]):
            if "test_" not in rel:
                model_files.append(rel)
    model_files = sorted(set(model_files))
    add_finding(
        fid="WF-006", wave=3, severity="OBSERVATION", title=f"Model universe size ({len(model_files)} candidates)",
        desc="Large model/decision-engine surface requires tiered validation; none validated at Wave 3.",
        evidence=[], status="NOT VERIFIED",
    )
    return {"model_candidates": len(model_files), "sample": model_files[:40]}


# --- WAVE 7: Security quick scan ---
def wave7() -> dict:
    secrets_hits = grep_count(r"(api[_-]?key|secret|password)\s*=\s*['\"][^'\"]+['\"]", ".")
    eval_hits = grep_count(r"\beval\(", ".")
    exec_hits = grep_count(r"\bexec\(", ".")
    e = add_evidence("hardcoded secret pattern scan", "rg", f"matches={secrets_hits}")
    if secrets_hits > 0:
        add_finding(
            fid="WF-007", wave=7, severity="P1", title="Potential hardcoded secret patterns",
            desc=f"rg found {secrets_hits} lines matching secret assignment heuristics — manual review required.",
            evidence=[e], status="NOT VERIFIED",
        )
    return {"secret_pattern_hits": secrets_hits, "eval_hits": eval_hits, "exec_hits": exec_hits}


# --- WAVE 12: Tests ---
def wave12() -> dict:
    skipped = grep_count(r"@pytest\.mark\.skip|pytest\.skip\(", "tests")
    xfail = grep_count(r"@pytest\.mark\.xfail", "tests")
    add_finding(
        fid="WF-008", wave=12, severity="OBSERVATION", title="Test suite scale vs verification gap",
        desc="1054 test functions discovered; zero runtime test execution in this audit session.",
        evidence=[], status="NOT VERIFIED",
    )
    return {"test_functions": 1054, "skip_markers": skipped, "xfail_markers": xfail, "tests_executed": 0}


# --- WAVE 17: Documentation contradictions ---
def wave17() -> dict:
    freeze = ROOT / "docs/BATCH07_FINAL_LOCAL_FREEZE.json"
    contradictions = []
    if freeze.is_file():
        data = json.loads(freeze.read_text())
        if data.get("BATCH07_FINAL_LOCAL_FREEZE") is True:
            contradictions.append({
                "type": "Docs claim CLOSED vs Audit zero-trust",
                "doc": str(freeze),
                "claim": "BATCH07_FINAL_LOCAL_FREEZE=true",
                "code": "Independent E1 verification not performed",
            })
    add_finding(
        fid="WF-009", wave=17, severity="P2", title="Documentation-institutional freeze claims unrevalidated",
        desc="Batch07 freeze JSON asserts closure; audit has no E1/E2 corroboration.",
        evidence=["EVD-006"], status="NOT VERIFIED",
    )
    return {"contradictions": contradictions}


# --- WAVE 20: Hidden failures ---
def wave20() -> dict:
    fail_open = grep_count(r"except\s*:\s*pass|except Exception:\s*pass", ".")
    return_zero = grep_count(r"return\s+0(?:\.0)?\s*$", ".")
    e = add_evidence("silent exception swallow scan", "rg", str(fail_open))
    if fail_open > 10:
        add_finding(
            fid="WF-010", wave=20, severity="P1", title="Silent exception swallowing patterns",
            desc=f"{fail_open} bare/silent except-pass patterns — potential fail-open behavior.",
            evidence=[e], status="NOT VERIFIED",
        )
    return {"silent_except_pass": fail_open, "return_zero_lines": return_zero}


def run_all() -> dict:
    results = {}
    results["wave2"] = wave2()
    results["wave3"] = wave3()
    results["wave7"] = wave7()
    results["wave12"] = wave12()
    results["wave17"] = wave17()
    results["wave20"] = wave20()

    # Stub other waves with NOT VERIFIED status
    for w in [4, 5, 6, 8, 9, 10, 11, 13, 14, 15, 16, 18, 19, 21, 22]:
        results[f"wave{w}"] = {"status": "NOT VERIFIED", "note": "Requires dedicated wave execution"}

    save_json("WAVES_02_22_ANALYSIS.json", results)
    save_json("WAVE_FINDINGS_ACCUMULATED.json", findings)
    save_json("WAVE_EVIDENCE_ACCUMULATED.json", evidence)
    return results


if __name__ == "__main__":
    print(json.dumps(run_all(), indent=2)[:4000])
