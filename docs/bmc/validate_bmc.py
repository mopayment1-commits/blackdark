#!/usr/bin/env python3
"""BMC constitutional proof validator."""

from __future__ import annotations

import re
import sys
from pathlib import Path

BMC_DIR = Path(__file__).resolve().parent

FORBIDDEN_PATTERNS = [
    r"\bHTTP\b",
    r"\bREST\b",
    r"\bSSE\b",
    r"\bCI\b",
    r"\bDocker\b",
    r"\bdocker\b",
    r"\bcompose\b",
    r"\bPython\b",
    r"\bpython\b",
    r"\blint\b",
    r"\bmerge\b",
    r"\bmodule\b",
    r"\bimport\b",
    r"\bP0[0-9]+\b",
    r"\bP1[0-9]+\b",
    r"docs/",
    r"\.py\b",
    r"\.md\b",
    r"\bbiec\b",
    r"\bBIEC\b",
]

LEVEL_PREFIXES = {
    0: ("META_CONSTITUTION.md", re.compile(r"ART-META-\d+")),
    1: ("AUTHORITY_CONSTITUTION.md", re.compile(r"ART-AUTH-\d+")),
    2: ("IDENTITY_CONSTITUTION.md", re.compile(r"ART-ID-\d+")),
    3: ("DERIVATION_CONSTITUTION.md", re.compile(r"ART-DER-\d+")),
}

LEVEL4_FILES = [
    "ENGINEERING_CONSTITUTION.md",
    "ARCHITECTURE_CONSTITUTION.md",
    "FINANCIAL_CONSTITUTION.md",
    "SECURITY_CONSTITUTION.md",
    "AI_CONSTITUTION.md",
    "DATA_CONSTITUTION.md",
    "PLATFORM_CONSTITUTION.md",
    "GOVERNANCE_CONSTITUTION.md",
    "QUALITY_CONSTITUTION.md",
]

ARTICLE_HEADER = re.compile(r"^### (ART-[A-Z]+-\d+)\s*$", re.MULTILINE)
PRINCIPLE_RE = re.compile(r"\| Principle \| (.+) \|")
RULE_RE = re.compile(r"\| Rule \| (.+) \|")
DERIVES_RE = re.compile(r"\| Derives from \| (.+) \|")
ART_ID_RE = re.compile(r"ART-[A-Z]+-\d+")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def article_level(art_id: str) -> int | None:
    if art_id.startswith("ART-META-"):
        return 0
    if art_id.startswith("ART-AUTH-"):
        return 1
    if art_id.startswith("ART-ID-"):
        return 2
    if art_id.startswith("ART-DER-"):
        return 3
    return 4


def parse_articles(content: str) -> dict[str, dict[str, str]]:
    articles: dict[str, dict[str, str]] = {}
    matches = list(ARTICLE_HEADER.finditer(content))
    for i, match in enumerate(matches):
        art_id = match.group(1)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = content[start:end]
        principle = ""
        derives = ""
        m = PRINCIPLE_RE.search(body)
        if m:
            principle = m.group(1).strip()
        else:
            m = RULE_RE.search(body)
            if m:
                principle = m.group(1).strip()
        m = DERIVES_RE.search(body)
        if m:
            derives = m.group(1).strip()
        articles[art_id] = {"principle": principle, "derives": derives, "body": body}
    return articles


def main() -> int:
    defects: list[str] = []
    all_articles: dict[str, dict[str, str]] = {}
    corpus_parts: list[str] = []

    for fname, _ in LEVEL_PREFIXES.values():
        path = BMC_DIR / fname
        if not path.exists():
            defects.append(f"Missing required constitution file: {fname}")
            continue
        text = read(path)
        corpus_parts.append(text)
        all_articles.update(parse_articles(text))

    for fname in LEVEL4_FILES:
        path = BMC_DIR / fname
        if not path.exists():
            defects.append(f"Missing required constitution file: {fname}")
            continue
        text = read(path)
        corpus_parts.append(text)
        all_articles.update(parse_articles(text))

    corpus = "\n".join(corpus_parts)

    # Forbidden content
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, corpus):
            defects.append(f"Forbidden pattern detected: {pattern}")

    # Duplicate principles
    principles: dict[str, list[str]] = {}
    for art_id, data in all_articles.items():
        p = data["principle"]
        if not p:
            defects.append(f"Missing principle: {art_id}")
            continue
        principles.setdefault(p, []).append(art_id)
    for principle, ids in principles.items():
        if len(ids) > 1:
            defects.append(f"Duplicated principle across {', '.join(ids)}")

    # Derivation level constraint
    for art_id, data in all_articles.items():
        if article_level(art_id) != 4:
            continue
        if not data["derives"]:
            defects.append(f"Level 4 article missing Derives from: {art_id}")
            continue
        for ref in ART_ID_RE.findall(data["derives"]):
            ref_level = article_level(ref)
            if ref_level is None or ref_level > 3:
                defects.append(f"{art_id} derives from invalid or Level 4 source: {ref}")

    # Level 0-3 must not derive from Level 4
    for art_id, data in all_articles.items():
        lvl = article_level(art_id)
        if lvl is None or lvl > 3:
            continue
        for ref in ART_ID_RE.findall(data["derives"]):
            if article_level(ref) == 4:
                defects.append(f"{art_id} illegally derives from Level 4: {ref}")

    # Circular dependency via derives graph (only upward allowed)
    graph: dict[str, set[str]] = {}
    for art_id, data in all_articles.items():
        graph[art_id] = set(ART_ID_RE.findall(data["derives"]))

    visiting: set[str] = set()
    visited: set[str] = set()
    stack: set[str] = set()

    def dfs(node: str) -> bool:
        if node in stack:
            return True
        if node in visited:
            return False
        visited.add(node)
        stack.add(node)
        for nbr in graph.get(node, set()):
            if dfs(nbr):
                return True
        stack.remove(node)
        return False

    for node in graph:
        visiting.clear()
        if dfs(node):
            defects.append(f"Circular derivation dependency detected involving {node}")
            break

    # Supremacy singularity
    supremacy = [a for a, d in all_articles.items() if "only supreme governing authority" in d["principle"].lower()]
    if len(supremacy) != 1:
        defects.append(f"Supremacy article count must be 1, found {len(supremacy)}: {supremacy}")

    # Required derivation rules for identity classes
    required_outputs = {
        "FEATURE_IDENTITY",
        "CAPABILITY_IDENTITY",
        "PLATFORM_IDENTITY",
        "SERVICE_IDENTITY",
        "ARTIFACT",
        "DECISION",
        "EVIDENCE",
        "DATASET_IDENTITY",
        "MODEL_IDENTITY",
        "FINDING",
        "CONTROL",
        "TEST",
        "GOVERNANCE_DECISION",
        "FEATURE_CAPABILITY_BINDING",
        "DERIVATION_ENFORCEMENT",
    }
    found_outputs: set[str] = set()
    for data in all_articles.values():
        m = re.search(r"\| Output class \| (.+?) \|", data["body"])
        if m:
            found_outputs.add(m.group(1).strip())
    missing_outputs = required_outputs - found_outputs
    if missing_outputs:
        defects.append(f"Missing derivation output classes: {sorted(missing_outputs)}")

    # Amendment rule present
    if not any("amendment record" in d["principle"].lower() for d in all_articles.values()):
        defects.append("Missing amendment rule in Level 0")

    # Interpretation rule present
    if not any("term meaning resolves exclusively" in d["principle"].lower() for d in all_articles.values()):
        defects.append("Missing interpretation rule in Level 0")

    # Identity classes
    required_identities = [
        "Feature identity",
        "Capability identity",
        "Platform identity",
        "Service identity",
        "Artifact identity",
        "Decision identity",
        "Evidence identity",
        "Dataset identity",
        "Model identity",
        "User identity",
        "Tenant identity",
    ]
    for ident in required_identities:
        if ident not in corpus:
            defects.append(f"Missing identity class definition: {ident}")

    if defects:
        print("BLACKDARK META CONSTITUTION REOPENED")
        for d in sorted(set(defects)):
            print(f"- {d}")
        return 1

    print("BLACKDARK META CONSTITUTION VERIFIED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
