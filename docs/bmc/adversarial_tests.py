#!/usr/bin/env python3
"""Eight adversarial constitutional tests for BMC."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from validate_bmc import (
    ART_ID_RE,
    BMC_DIR,
    LEVEL4_FILES,
    LEVEL_PREFIXES,
    article_level,
    parse_articles,
    read,
)

BIEC_ARCHIVE = Path(__file__).resolve().parent.parent / "biec" / "ARCHIVED_REFERENCE_ONLY.md"

FORBIDDEN_TECH = [
    r"\bHTTP\b",
    r"\bREST\b",
    r"\bSSE\b",
    r"\bCI\b",
    r"\bDocker\b",
    r"\bdocker\b",
    r"\bPython\b",
    r"\bpython\b",
    r"\blint\b",
    r"\bmerge\b",
    r"\bmodule\b",
    r"\bimport\b",
    r"\bOpenAPI\b",
    r"\bgithub\b",
    r"\bgit\b",
    r"\bpytest\b",
    r"\bnpm\b",
    r"\bpip\b",
]

ENUMERATION_PATTERNS = [
    r"\bP0[0-9]+\b",
    r"\bP1[0-9]+\b",
    r"\bFCP-\d+\b",
    r"\bCAP-\d+\b",
    r"\bfeature[_-]\d+\b",
    r"^\s*[-*]\s+[A-Z][A-Za-z0-9_/-]+\s*$",
]

COMPETING_SUPREMACY = [
    r"only supreme governing authority",
    r"sole governing authority",
    r"only governing authority",
    r"supreme authority for all",
]


def load_corpus() -> tuple[str, dict[str, dict[str, str]]]:
    parts: list[str] = []
    articles: dict[str, dict[str, str]] = {}
    for fname, _ in LEVEL_PREFIXES.values():
        text = read(BMC_DIR / fname)
        parts.append(text)
        articles.update(parse_articles(text))
    for fname in LEVEL4_FILES:
        text = read(BMC_DIR / fname)
        parts.append(text)
        articles.update(parse_articles(text))
    return "\n".join(parts), articles


def normalize(text: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    stop = {"the", "a", "an", "and", "or", "per", "under", "with", "without", "from", "to", "is", "are", "must", "may", "not", "one", "all", "each", "any", "when", "only", "through", "yields", "fail", "declared", "record", "class", "identity", "authority"}
    return {t for t in tokens if t not in stop and len(t) > 2}


def token_overlap(a: str, b: str) -> float:
    sa, sb = normalize(a), normalize(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


@dataclass
class AdversarialResult:
    test_id: str
    name: str
    passed: bool
    defects: list[str] = field(default_factory=list)


def adv_001_duplicate_law_attack(articles: dict[str, dict[str, str]]) -> AdversarialResult:
    result = AdversarialResult("ADV-001", "Duplicate Law Attack", True)
    ids = sorted(articles)
    for i, a in enumerate(ids):
        for b in ids[i + 1 :]:
            pa, pb = articles[a]["principle"], articles[b]["principle"]
            if not pa or not pb:
                continue
            if pa == pb:
                result.passed = False
                result.defects.append(f"Exact duplicate principle: {a} and {b}")
            elif token_overlap(pa, pb) >= 0.82:
                result.passed = False
                result.defects.append(f"Near-duplicate principle ({token_overlap(pa, pb):.2f}): {a} vs {b}")
    return result


def adv_002_contradiction_attack(articles: dict[str, dict[str, str]]) -> AdversarialResult:
    result = AdversarialResult("ADV-002", "Contradiction Attack", True)
    exclusivity_one: list[str] = []
    multiplicity: list[str] = []
    for art_id, data in articles.items():
        p = data["principle"].lower()
        if re.search(r"\bexactly one\b|\bat most one\b|\bsole\b|\bonly one\b", p):
            exclusivity_one.append(art_id)
        if re.search(r"\bmultiple\b|\bat least two\b|\bplural\b", p) and "multiple primary" not in p and "zero or multiple" not in data.get("body", ""):
            multiplicity.append(art_id)
    pairs = [
        ("canonical public price authority", "internal aggregation entry"),
        ("master execution authorization authority", "ad hoc tier check"),
        ("supreme governing authority", "competing execution-authority"),
    ]
    corpus = " ".join(d["principle"].lower() for d in articles.values())
    for a, b in pairs:
        if a in corpus and b in corpus:
            for x in exclusivity_one:
                for y in exclusivity_one:
                    if x != y and token_overlap(articles[x]["principle"], articles[y]["principle"]) > 0.75:
                        if "access" in articles[x]["principle"].lower() and "access" in articles[y]["principle"].lower():
                            result.passed = False
                            result.defects.append(f"Potential duplicated exclusivity on access domain: {x} vs {y}")
    return result


def adv_003_hidden_authority_attack(articles: dict[str, dict[str, str]]) -> AdversarialResult:
    result = AdversarialResult("ADV-003", "Hidden Authority Attack", True)
    for art_id, data in articles.items():
        if art_id.startswith("ART-ID-"):
            continue
        body = data["body"]
        for line in body.splitlines():
            if "Verification predicate" not in line:
                continue
            if "declared" not in line.lower():
                continue
            if "authority" in line.lower() or "ART-AUTH-" in body:
                continue
            if "undeclared" in line.lower():
                continue
            result.passed = False
            result.defects.append(f"Undeclared parameter without authority linkage: {art_id} -> {line.strip()}")
    return result


def adv_004_technology_leak_attack(corpus: str) -> AdversarialResult:
    result = AdversarialResult("ADV-004", "Technology Leak Attack", True)
    for pattern in FORBIDDEN_TECH:
        if re.search(pattern, corpus, re.IGNORECASE):
            result.passed = False
            result.defects.append(f"Forbidden technology pattern: {pattern}")
    if re.search(r"\bcompose\b", corpus) and not re.search(r"\bdecomposition\b", corpus):
        pass
    elif re.search(r"\bcompose\b", corpus):
        for m in re.finditer(r".{0,30}compose.{0,30}", corpus, re.IGNORECASE):
            if "decomposition" not in m.group(0).lower():
                result.passed = False
                result.defects.append(f"Forbidden compose reference: {m.group(0)!r}")
    return result


def adv_005_derivation_bypass_attack(articles: dict[str, dict[str, str]]) -> AdversarialResult:
    result = AdversarialResult("ADV-005", "Derivation Bypass Attack", True)
    known = set(articles)
    for art_id, data in articles.items():
        lvl = article_level(art_id)
        if lvl == 4 and not data["derives"]:
            result.passed = False
            result.defects.append(f"Level 4 article without derivation chain: {art_id}")
        for ref in ART_ID_RE.findall(data["derives"]):
            if ref not in known:
                result.passed = False
                result.defects.append(f"Broken derivation reference: {art_id} -> {ref}")
            if lvl == 4 and article_level(ref) == 4:
                result.passed = False
                result.defects.append(f"Level 4 cross-derivation bypass: {art_id} -> {ref}")
        if lvl is not None and lvl <= 3:
            for ref in ART_ID_RE.findall(data["derives"]):
                if article_level(ref) == 4:
                    result.passed = False
                    result.defects.append(f"Lower level illegally cites Level 4: {art_id} -> {ref}")
        if "Verification predicate" in data["body"] and "FAIL" not in data["body"]:
            result.passed = False
            result.defects.append(f"Missing FAIL semantics: {art_id}")
    return result


def adv_006_circular_dependency_attack(articles: dict[str, dict[str, str]]) -> AdversarialResult:
    result = AdversarialResult("ADV-006", "Circular Dependency Attack", True)
    graph = {art_id: set(ART_ID_RE.findall(data["derives"])) for art_id, data in articles.items()}
    stack: set[str] = set()
    visited: set[str] = set()

    def dfs(node: str) -> bool:
        if node in stack:
            return True
        if node in visited:
            return False
        visited.add(node)
        stack.add(node)
        for nbr in graph.get(node, ()):
            if nbr in graph and dfs(nbr):
                return True
        stack.remove(node)
        return False

    for node in graph:
        stack.clear()
        if dfs(node):
            result.passed = False
            result.defects.append(f"Circular derivation cycle detected at {node}")
            break
    return result


def adv_007_enumeration_injection_attack(corpus: str) -> AdversarialResult:
    result = AdversarialResult("ADV-007", "Enumeration Injection Attack", True)
    for pattern in ENUMERATION_PATTERNS:
        if re.search(pattern, corpus, re.MULTILINE | re.IGNORECASE):
            result.passed = False
            result.defects.append(f"Forbidden enumeration pattern: {pattern}")
    if re.search(r"\b sixteen\b|\bsixteen platforms\b|\b16 platforms\b", corpus, re.IGNORECASE):
        result.passed = False
        result.defects.append("Fixed platform count enumeration detected")
    return result


def adv_008_supremacy_hijack_attack(articles: dict[str, dict[str, str]], corpus: str) -> AdversarialResult:
    result = AdversarialResult("ADV-008", "Supremacy Hijack Attack", True)
    supremacy_principles = [
        art_id
        for art_id, data in articles.items()
        if any(re.search(p, data["principle"], re.IGNORECASE) for p in COMPETING_SUPREMACY)
    ]
    if len(supremacy_principles) != 1:
        result.passed = False
        result.defects.append(f"Supremacy hijack: expected 1 supremacy principle, found {supremacy_principles}")
    if not BIEC_ARCHIVE.exists():
        result.passed = False
        result.defects.append("BIEC archive manifest missing")
    else:
        archive = read(BIEC_ARCHIVE)
        if "ARCHIVED_REFERENCE_ONLY" not in archive or "Governing authority | NONE" not in archive:
            result.passed = False
            result.defects.append("BIEC archive does not revoke governing authority")
    if re.search(r"\bBIEC\b", corpus):
        result.passed = False
        result.defects.append("Superseded BIEC reference inside active BMC corpus")
    sole_level_markers = re.findall(r"\*\*Document role:\*\* Sole [^\n]+", corpus)
    if len(sole_level_markers) != 4:
        result.passed = False
        result.defects.append(
            f"Expected 4 sole domain markers at Levels 0-3, found {len(sole_level_markers)}: {sole_level_markers}"
        )
    return result


def run_adversarial_tests() -> list[AdversarialResult]:
    corpus, articles = load_corpus()
    return [
        adv_001_duplicate_law_attack(articles),
        adv_002_contradiction_attack(articles),
        adv_003_hidden_authority_attack(articles),
        adv_004_technology_leak_attack(corpus),
        adv_005_derivation_bypass_attack(articles),
        adv_006_circular_dependency_attack(articles),
        adv_007_enumeration_injection_attack(corpus),
        adv_008_supremacy_hijack_attack(articles, corpus),
    ]


def main() -> int:
    results = run_adversarial_tests()
    failed = [r for r in results if not r.passed]
    if failed:
        print("ADVERSARIAL TESTS FAILED")
        for r in failed:
            print(f"\n{r.test_id} {r.name}: FAIL")
            for d in r.defects:
                print(f"  - {d}")
        return 1
    print("ADVERSARIAL TESTS PASSED (8/8)")
    for r in results:
        print(f"  {r.test_id} {r.name}: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
