#!/usr/bin/env python3
"""Build CAP978 catalog from Project_978 PDF (646 base + 332 extension)."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import fitz

PDF = Path("/home/ubuntu/.cursor/projects/workspace/uploads/Project_978_Capabilities_Grouped_b618.pdf")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "cap978"

TRACKS = {
    "T01": "Foundation, Architecture & Reliability",
    "T02": "Security, Privacy, Identity & Compliance",
    "T03": "Data Platform, Quality & Connectors",
    "T04": "Market Data, Pricing & Liquidity",
    "T05": "Derivatives, Funding & Liquidations",
    "T06": "Arbitrage, Execution & Trading Systems",
    "T07": "Portfolio, Allocation & Treasury",
    "T08": "Risk, Hedging & Stress Analytics",
    "T09": "On-Chain, Wallet, Whale & Entity Intelligence",
    "T10": "DeFi, Yield, Stablecoins & Token Economics",
    "T11": "Technical, Quant & Predictive Analytics",
    "T12": "AI, Sentiment, News & Decision Intelligence",
    "T13": "Alerts, Automation & User Workflows",
    "T14": "UX, Dashboards, Visualization & Beginner Experience",
    "T15": "Institutional, B2B, API & Developer Platform",
    "T16": "Billing, Subscription, Tenant & Business Operations",
    "T17": "Reporting, Audit, Tax & Governance",
    "T18": "Unmapped PDF Extension Track",
    "T19": "978 Extension — Pasted Markdown Scope",
}

FRAG = {
    "Detection", "Rate", "Analysis", "Engine", "Intelligence", "Layer", "Data", "Portfolio",
    "Footer", "Export", "Testing", "Delivery", "Workspace", "Analytics", "Logic", "Read",
}


def split_en_ar(text: str) -> str:
    m = re.search(r"[\u0600-\u06FF]", text)
    return text[: m.start()].strip() if m else text.strip()


def extract_page(doc: fitz.Document, page_num: int) -> list[str]:
    rows: dict[int, list[tuple[float, str]]] = defaultdict(list)
    for b in doc[page_num - 1].get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        for line in b["lines"]:
            rows[round(line["bbox"][1] / 10) * 10].append(
                (line["bbox"][0], "".join(sp["text"] for sp in line["spans"]).strip())
            )
    names: list[str] = []
    for key in sorted(rows.keys()):
        left = ""
        for x, raw in sorted(rows[key], key=lambda t: t[0]):
            if x < 180:
                en = split_en_ar(raw)
                if en:
                    left = (left + " " + en).strip()
        left = re.sub(r"\s+", " ", left).strip(" /")
        if not left or left in ("الميزة", "الهدف", "#") or left.startswith("Column"):
            continue
        if left == "Column2 Column3":
            left = "Market Compass / Market Regime Engine"
        names.append(left)
    out: list[str] = []
    for n in names:
        if out and (n in FRAG or n.startswith("not ")):
            out[-1] = (out[-1] + " " + n).strip()
        elif out and (
            out[-1].endswith("/")
            or out[-1].endswith("(")
            or out[-1].endswith("_P")
            or out[-1].endswith("DD")
            or out[-1].endswith("Compliance")
        ):
            out[-1] = (out[-1] + " " + n).strip()
        else:
            out.append(n)
    return out


def parse_index(doc: fitz.Document) -> dict[int, str]:
    index: dict[int, str] = {}
    for p in range(33):
        text = doc[p].get_text()
        for m in re.finditer(r"(\d{1,3})\s+(T\d{2})\s*\n", text):
            cid = int(m.group(1))
            if cid <= 646:
                index[cid] = m.group(2)
        for m in re.finditer(r"(\d{1,3})\s*\n(T\d{2})\s*\n", text):
            cid = int(m.group(1))
            if cid <= 646:
                index[cid] = m.group(2)
    return index


def build_base_catalog() -> list[dict]:
    base_path = ROOT / "docs" / "cap646" / "CAP646_CATALOG.json"
    if not base_path.is_file():
        raise RuntimeError(f"Missing base catalog: {base_path}")
    rows = json.loads(base_path.read_text(encoding="utf-8"))
    if len(rows) != 646:
        raise RuntimeError(f"Expected 646 base rows, got {len(rows)}")
    for row in rows:
        row["scope"] = "base_646"
    return rows


def build_extension_catalog(doc: fitz.Document) -> list[dict]:
    """IDs 647–978 from pasted-markdown extension pages."""
    names: list[str] = []
    for pg in range(67, doc.page_count + 1):
        page_names = extract_page(doc, pg)
        # Skip dense requirement-only pages (mostly lowercase bullets)
        filtered = [n for n in page_names if len(n) >= 4 and not n.startswith("No ")]
        if filtered:
            names.extend(filtered)
    # Deduplicate consecutive duplicates while preserving order
    deduped: list[str] = []
    for n in names:
        if not deduped or deduped[-1].lower() != n.lower():
            deduped.append(n)
    if len(deduped) < 332:
        raise RuntimeError(f"Expected >=332 extension names, got {len(deduped)}")
    ext_names = deduped[:332]
    catalog = []
    for offset, name in enumerate(ext_names):
        cid = 647 + offset
        catalog.append(
            {
                "id": cid,
                "track": "T19",
                "track_name": TRACKS["T19"],
                "capability": name,
                "scope": "extension_647_978",
                "name_source": "pdf_978_pasted_markdown",
            }
        )
    return catalog


def main() -> None:
    if not PDF.is_file():
        print(f"Missing PDF: {PDF}", file=sys.stderr)
        sys.exit(1)
    doc = fitz.open(str(PDF))
    base = build_base_catalog()
    ext = build_extension_catalog(doc)
    catalog = base + ext
    if len(catalog) != 978:
        raise RuntimeError(f"Expected 978 catalog rows, got {len(catalog)}")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "CAP978_CATALOG.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    meta = {
        "total": 978,
        "base_646": 646,
        "extension_647_978": 332,
        "tracks": dict(Counter(r["track"] for r in catalog)),
        "source_pdf": str(PDF),
    }
    (OUT / "CAP978_META.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("OK", meta)


if __name__ == "__main__":
    main()
