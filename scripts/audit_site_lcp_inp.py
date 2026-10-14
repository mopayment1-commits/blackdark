#!/usr/bin/env python3
"""Audit LCP (per sitemap page) and click latency (per visible button)."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

LCP_MAX_MS = 2500
INP_MAX_MS = 200


def fetch_sitemap_urls(base: str, timeout: float = 30.0) -> list[str]:
    base = base.rstrip("/")
    req = urllib.request.Request(f"{base}/sitemap.xml", headers={"Accept": "application/xml"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        xml = resp.read()
    root = ET.fromstring(xml)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locs = [el.text.strip() for el in root.findall(".//sm:loc", ns)]
    if not locs:
        locs = [el.text.strip() for el in root.iter() if el.tag.endswith("loc") and el.text]
    return locs


def normalize_urls_to_base(base: str, urls: list[str]) -> list[str]:
    base = base.rstrip("/")
    out: list[str] = []
    seen: set[str] = set()
    for raw in urls:
        path = urllib.parse.urlparse(raw).path or "/"
        if not path.startswith("/"):
            path = "/" + path
        url = f"{base}{path}"
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out


def playwright_lcp_ms(url: str) -> tuple[float | None, str | None]:
    probe = Path(__file__).resolve().parent / "audit_lcp_playwright.mjs"
    try:
        proc = subprocess.run(
            ["node", str(probe), url],
            capture_output=True,
            text=True,
            timeout=90,
        )
        line = (proc.stdout or "").strip().splitlines()[-1] if proc.stdout else ""
        data = json.loads(line) if line else {}
        if data.get("error"):
            return None, data["error"][:400]
        lcp = data.get("lcp_ms")
        return (float(lcp), None) if lcp is not None else (None, "no LCP from playwright")
    except Exception as exc:
        return None, str(exc)


def lighthouse_lcp_ms(url: str, chrome_flags: str) -> tuple[float | None, str | None]:
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        out_path = tmp.name
    try:
        cmd = [
            "npx",
            "--yes",
            "lighthouse",
            url,
            "--only-audits=largest-contentful-paint",
            "--output=json",
            f"--output-path={out_path}",
            "--quiet",
            f"--chrome-flags={chrome_flags}",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "lighthouse failed")[:500]
            return None, err
        data = json.loads(Path(out_path).read_text(encoding="utf-8"))
        audit = data.get("audits", {}).get("largest-contentful-paint", {})
        runtime = data.get("runtimeError")
        if runtime:
            return None, str(runtime)
        numeric = audit.get("numericValue")
        if numeric is None:
            return None, "no LCP numericValue"
        return float(numeric), None
    except subprocess.TimeoutExpired:
        return None, "lighthouse timeout"
    except Exception as exc:
        return None, str(exc)
    finally:
        Path(out_path).unlink(missing_ok=True)


def playwright_button_inp(page_url: str, inp_max_ms: int) -> dict:
    probe = Path(__file__).resolve().parent / "audit_inp_probe.mjs"
    proc = subprocess.run(
        ["node", str(probe), page_url, str(inp_max_ms)],
        capture_output=True,
        text=True,
        timeout=90,
        cwd=str(Path(__file__).resolve().parents[1]),
    )
    line = (proc.stdout or "").strip().splitlines()[-1] if proc.stdout else ""
    try:
        return json.loads(line) if line else {"buttons": [], "error": proc.stderr[:300]}
    except json.JSONDecodeError:
        return {"buttons": [], "error": (proc.stderr or proc.stdout or "playwright parse error")[:300]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="https://blackdark.io")
    parser.add_argument("--chrome-flags", default="--headless --no-sandbox --disable-gpu")
    parser.add_argument("--skip-inp", action="store_true")
    parser.add_argument("--skip-lcp", action="store_true")
    parser.add_argument(
        "--lcp-engine",
        choices=("lighthouse", "playwright", "auto"),
        default="auto",
        help="auto = lighthouse then playwright fallback",
    )
    parser.add_argument("--max-pages", type=int, default=0, help="0 = all")
    parser.add_argument("--output", default="")
    parser.add_argument(
        "--paths-from-app",
        action="store_true",
        help="Use dashboard TestClient sitemap paths (when live sitemap fetch fails)",
    )
    args = parser.parse_args()

    try:
        urls = normalize_urls_to_base(args.base, fetch_sitemap_urls(args.base))
    except Exception as exc:
        if not args.paths_from_app:
            raise
        urls = []
        print(f"sitemap fetch failed ({exc}); using app paths", file=sys.stderr)
    if args.paths_from_app or not urls:
        root = Path(__file__).resolve().parents[1]
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from fastapi.testclient import TestClient
        from dashboard import app as dash_app

        xml = TestClient(dash_app).get("/sitemap.xml").text
        import re

        locs = re.findall(r"<loc>([^<]+)", xml)
        urls = normalize_urls_to_base(args.base, locs)
    if args.max_pages:
        urls = urls[: args.max_pages]

    report = {
        "base": args.base,
        "lcp_threshold_ms": LCP_MAX_MS,
        "inp_threshold_ms": INP_MAX_MS,
        "pages": [],
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    all_ok = True

    for url in urls:
        row = {"url": url, "lcp_ms": None, "lcp_s": None, "lcp_error": None, "buttons": []}
        if not args.skip_lcp:
            lcp_ms, err = None, None
            if args.lcp_engine in ("lighthouse", "auto"):
                lcp_ms, err = lighthouse_lcp_ms(url, args.chrome_flags)
            if (lcp_ms is None or args.lcp_engine == "playwright") and args.lcp_engine != "lighthouse":
                pw_ms, pw_err = playwright_lcp_ms(url)
                if pw_ms is not None:
                    lcp_ms, err = pw_ms, None
                elif lcp_ms is None:
                    err = err or pw_err
            row["lcp_ms"] = round(lcp_ms, 1) if lcp_ms is not None else None
            row["lcp_s"] = round(lcp_ms / 1000, 2) if lcp_ms is not None else None
            row["lcp_error"] = err
            if lcp_ms is None or lcp_ms > LCP_MAX_MS:
                all_ok = False
                row["lcp_over"] = True
            else:
                row["lcp_over"] = False
        if not args.skip_inp:
            inp = playwright_button_inp(url, INP_MAX_MS)
            row["inp_error"] = inp.get("error")
            for b in inp.get("buttons") or []:
                row["buttons"].append(b)
                if b.get("inp_ms") is None or b.get("inp_ms", 0) > INP_MAX_MS:
                    all_ok = False
            if inp.get("error"):
                all_ok = False
        report["pages"].append(row)
        print(f"done {url} LCP={row.get('lcp_s')}s buttons={len(row.get('buttons', []))}", file=sys.stderr)

    out_json = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(out_json, encoding="utf-8")
    print(out_json)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
