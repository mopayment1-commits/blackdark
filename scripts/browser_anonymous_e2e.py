#!/usr/bin/env python3
"""Real browser E2E capture for anonymous public surfaces."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PRIVATE_PREFIXES = (
    "/api/user",
    "/api/privacy",
    "/api/admin",
    "/api/data-governance",
    "/api/discipline-mirror/me",
    "/api/analytics/view",
)


def main() -> int:
    os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/browser-e2e.db")
    os.environ.setdefault("ENV", "development")
    os.environ.setdefault("COOKIE_SECURE", "false")
    os.environ.setdefault("SECRETS_MASTER_KEY", "browser-e2e-key")
    os.environ.setdefault("SESSION_TOKEN_PEPPER", "browser-e2e-pepper")
    os.environ.setdefault("ANONYMOUS_PUBLIC_RL_EXEMPT", "true")
    os.environ.setdefault("VIRAL_MODE", "false")
    os.environ.setdefault("VIRAL_API_RL_PER_MIN", "100000")
    os.environ.setdefault("VIRAL_WEB_RL_PER_MIN", "100000")
    os.environ.setdefault("VIRAL_ORACLE_RL_PER_MIN", "100000")

    from playwright.sync_api import sync_playwright

    port = 8765
    env = os.environ.copy()
    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "dashboard:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )
    base = f"http://127.0.0.1:{port}"
    for _ in range(30):
        try:
            import urllib.request

            urllib.request.urlopen(base + "/health/live", timeout=2)
            break
        except Exception:
            time.sleep(1)
    else:
        server.terminate()
        raise RuntimeError("server failed to become ready for browser E2E")
    console_errors: list[str] = []
    console_warnings: list[str] = []
    network_errors: list[str] = []
    http_error_responses: list[str] = []
    private_calls: list[dict[str, str]] = []
    third_party_sent: list[str] = []
    third_party_refs: list[str] = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 375, "height": 812})
            page = context.new_page()

            def on_console(msg):
                t = msg.type
                text = msg.text
                if t == "error":
                    console_errors.append(text)
                elif t == "warning":
                    console_warnings.append(text)

            def on_request(req):
                url = req.url
                if not url.startswith(base) and not url.startswith("data:"):
                    third_party_sent.append(f"{req.method} {url}")
                path = url.replace(base, "").split("?", 1)[0]
                for pref in PRIVATE_PREFIXES:
                    if path.startswith(pref):
                        private_calls.append(
                            {
                                "METHOD": req.method,
                                "URL": path,
                                "INITIATOR": "browser",
                                "EXPECTED_FOR_ANONYMOUS": "deny_or_gate",
                                "STATUS": "requested",
                            }
                        )

            def on_request_failed(req):
                if req.url.startswith(base):
                    network_errors.append(f"{req.method} {req.url} failed")

            def on_response(resp):
                if resp.url.startswith(base) and resp.status >= 400:
                    http_error_responses.append(f"{resp.status} {resp.request.method} {resp.url.replace(base, '')}")

            page.on("console", on_console)
            page.on("request", on_request)
            page.on("requestfailed", on_request_failed)
            page.on("response", on_response)

            for path in ("/", "/docs/public"):
                page.goto(base + path, wait_until="load", timeout=60000)
                time.sleep(1)

            page.set_viewport_size({"width": 375, "height": 812})
            page.goto(base + "/", wait_until="load", timeout=60000)
            time.sleep(2)

            refs = page.eval_on_selector_all(
                "link[href], script[src], img[src]",
                "els => els.map(e => e.href || e.src).filter(Boolean)",
            )
            for r in refs:
                if r and not r.startswith(base) and not r.startswith("data:"):
                    third_party_refs.append(r)

            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=10)

    unexpected_network = [e for e in network_errors if "401" in e or "403" in e or "failed" in e.lower()]
    out = {
        "REAL_BROWSER_E2E_RERUN": True,
        "PUBLIC_BROWSER_CONSOLE_ERRORS": console_errors,
        "PUBLIC_BROWSER_HTTP_ERROR_RESPONSES": sorted(set(http_error_responses)),
        "PUBLIC_BROWSER_WARNINGS": console_warnings,
        "PUBLIC_BROWSER_UNEXPECTED_NETWORK_ERRORS": unexpected_network,
        "ANONYMOUS_PAGE_PRIVATE_API_REQUESTS": private_calls,
        "THIRD_PARTY_REQUESTS_ACTUALLY_SENT": sorted(set(third_party_sent)),
        "THIRD_PARTY_RESOURCE_REFERENCES_ATTEMPTED": sorted(set(third_party_refs)),
    }
    out_path = ROOT / "docs" / "ANONYMOUS_BROWSER_E2E_EVIDENCE.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
