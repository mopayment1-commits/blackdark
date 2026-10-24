"""All explicit public HTML routes must return 200 HTML."""

from __future__ import annotations

from fastapi.testclient import TestClient

from anonymous_route_foundation import PUBLIC_HTML_EXACT


def test_all_public_html_exact_routes_render():
    from dashboard import app

    client = TestClient(app)
    pages = sorted({"/", "/login", *PUBLIC_HTML_EXACT})
    failures: list[str] = []
    for path in pages:
        res = client.get(path, headers={"Accept": "text/html"}, follow_redirects=False)
        if res.status_code in {301, 302, 307, 308}:
            loc = res.headers.get("location") or ""
            if loc.startswith("/"):
                res = client.get(loc.split("#")[0], headers={"Accept": "text/html"})
        ct = (res.headers.get("content-type") or "").lower()
        if res.status_code != 200 or "text/html" not in ct:
            failures.append(f"{path} -> {res.status_code} {ct[:40]}")
    assert not failures, "public HTML failures:\n" + "\n".join(failures[:20])
