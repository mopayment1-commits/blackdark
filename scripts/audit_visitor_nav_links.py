#!/usr/bin/env python3
"""Audit visitor-visible navigation links — zero JSON white-screen responses."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse, urljoin

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from anonymous_route_foundation import (  # noqa: E402
    PUBLIC_HTML_EXACT,
    PUBLIC_HTML_PREFIXES,
    is_anonymous_route_allowed,
)
from dashboard import app  # noqa: E402
from site_services import footer_manifest  # noqa: E402

SKIP_PREFIXES = ("mailto:", "tel:", "javascript:")
EXTERNAL_PREFIXES = ("http://", "https://", "//")
TEMPLATE_LITERAL = re.compile(r"\$\{")
HREF_RE = re.compile(r'<a\b[^>]*\bhref=["\']([^"\']+)["\']', re.I)


def _path_matches(path: str, exact: frozenset[str], prefixes: tuple[str, ...]) -> bool:
    if path in exact:
        return True
    return any(path.startswith(prefix) for prefix in prefixes)


def norm_path(href: str, base: str = "/") -> str | None:
    if not href or href.startswith("#") or href.startswith(SKIP_PREFIXES):
        return None
    if any(href.startswith(p) for p in EXTERNAL_PREFIXES):
        return None
    if TEMPLATE_LITERAL.search(href):
        return None
    if href.startswith("/"):
        u = urlparse(href)
        return u.path + (f"?{u.query}" if u.query else "")
    u = urlparse(urljoin(base, href))
    if not u.path.startswith("/"):
        return None
    return u.path + (f"?{u.query}" if u.query else "")


def seed_pages() -> list[str]:
    pages = sorted(
        {
            "/",
            "/login",
            "/oracle-accuracy",
            *PUBLIC_HTML_EXACT,
        }
    )
    fm = footer_manifest()
    for group in ("product", "trust", "company", "legal"):
        for item in fm.get(group, []):
            p = norm_path(str(item.get("href") or ""))
            if p:
                pages.append(p.split("#")[0].split("?")[0])
    return sorted(set(pages))


def extract_links(html: str, base: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for href in HREF_RE.findall(html):
        p = norm_path(href, base)
        if p:
            out.append((href, p))
    return out


def follow_to_html(client: TestClient, path: str, max_hops: int = 3) -> tuple[int, str, str]:
    current = path.split("#")[0] or "/"
    for _ in range(max_hops):
        res = client.get(current, headers={"Accept": "text/html"}, follow_redirects=False)
        ct = (res.headers.get("content-type") or "").lower()
        if res.status_code in {301, 302, 307, 308}:
            loc = res.headers.get("location") or ""
            if loc.startswith("/"):
                current = loc.split("#")[0] or "/"
                continue
            return res.status_code, ct, res.text[:160]
        return res.status_code, ct, res.text[:160]
    return 599, "", "redirect loop"


def is_allowed(status: int, ct: str, body: str) -> tuple[bool, str]:
    if "Anonymous access denied" in body:
        return False, "anon_json"
    if "application/json" in ct:
        return False, "json"
    if status == 404:
        return False, "404"
    if status == 200 and "text/html" in ct:
        return True, "html_200"
    if status == 401 and "text/html" in ct:
        return True, "html_login_gate"
    if status in {301, 302, 307, 308}:
        return True, "redirect"
    return False, f"status_{status}"


def main() -> int:
    client = TestClient(app)
    pages = seed_pages()
    discovered: dict[str, dict[str, str]] = {}
    results: list[dict[str, object]] = []

    for page in pages:
        res = client.get(page, headers={"Accept": "text/html"})
        if res.status_code != 200:
            status, ct, body = follow_to_html(client, page)
            ok, reason = is_allowed(status, ct, body)
            if not ok:
                results.append(
                    {
                        "source": page,
                        "href": page,
                        "path": page,
                        "status": status,
                        "content_type": ct,
                        "ok": False,
                        "reason": reason,
                    }
                )
            continue
        for href, path in extract_links(res.text, page):
            key = path.split("#")[0]
            if key not in discovered:
                discovered[key] = {"source": page, "href": href}

    for path, meta in sorted(discovered.items()):
        test_path = path.split("#")[0].split("?")[0]
        if not is_anonymous_route_allowed("GET", test_path):
            results.append(
                {
                    "source": meta["source"],
                    "href": meta["href"],
                    "path": test_path,
                    "status": None,
                    "content_type": "",
                    "ok": True,
                    "reason": "gated_skip",
                }
            )
            continue
        status, ct, body = follow_to_html(client, path.split("#")[0])
        ok, reason = is_allowed(status, ct, body)
        row = {
            "source": meta["source"],
            "href": meta["href"],
            "path": test_path,
            "status": status,
            "content_type": ct,
            "ok": ok,
            "reason": reason,
        }
        results.append(row)
        mark = "OK" if ok else "FAIL"
        print(f"{mark:4} GET {test_path:42} {status:3} {ct[:28]:28} reason={reason} src={meta['source']}")

    json_failures = [r for r in results if r["reason"] == "json" or r["reason"] == "anon_json"]
    dead = [r for r in results if not r["ok"]]
    print("\nSUMMARY")
    print("PUBLIC_NAV_JSON_RESPONSES =", len(json_failures))
    print("PUBLIC_DEAD_BUTTONS =", len(dead))
    print("TOTAL_LINKS =", len(results))
    out_path = ROOT / "artifacts" / "visitor_nav_audit.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"results": results, "summary": {
        "PUBLIC_NAV_JSON_RESPONSES": len(json_failures),
        "PUBLIC_DEAD_BUTTONS": len(dead),
        "TOTAL_LINKS": len(results),
    }}, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0 if not dead else 1


if __name__ == "__main__":
    raise SystemExit(main())
