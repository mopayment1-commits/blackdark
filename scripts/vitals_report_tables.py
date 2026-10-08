#!/usr/bin/env python3
"""Print markdown tables from audit_site_lcp_inp.json."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("json_path")
    args = parser.parse_args()
    data = json.loads(Path(args.json_path).read_text(encoding="utf-8"))
    pages = data.get("pages") or []

    print("### LCP by page\n")
    print("| Page | LCP (s) | OK (≤2.5s) |")
    print("|------|---------|------------|")
    for row in pages:
        path = row["url"].split("://", 1)[-1]
        if "/" in path:
            path = "/" + path.split("/", 1)[1]
        lcp_s = row.get("lcp_s")
        ok = lcp_s is not None and lcp_s <= 2.5
        disp = f"{lcp_s:.2f}" if lcp_s is not None else (row.get("lcp_error") or "—")
        print(f"| `{path}` | {disp} | {'yes' if ok else '**no**'} |")

    print("\n### INP by button\n")
    print("| Page | Button | INP (ms) | OK (≤200ms) |")
    print("|------|--------|----------|-------------|")
    for row in pages:
        path = row["url"].split("://", 1)[-1]
        if "/" in path:
            path = "/" + path.split("/", 1)[1]
        for b in row.get("buttons") or []:
            inp = b.get("inp_ms")
            label = (b.get("label") or "").replace("|", "\\|")
            ok = inp is not None and inp <= 200
            disp = str(inp) if inp is not None else (b.get("error") or "—")
            print(f"| `{path}` | {label} | {disp} | {'yes' if ok else '**no**'} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
