"""FastAPI route inventory + no-cookie probe helpers — AV §17."""

from __future__ import annotations

from typing import Any

from anonymous_visitor.allowlist import allowlist_export, is_anonymous_allowed, is_anonymous_denied, match_allowlist_entry
from anonymous_visitor.registry import classify_route


def scan_fastapi_routes(app: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for route in getattr(app, "routes", []):
        path = getattr(route, "path", None)
        if not path:
            continue
        methods = sorted(getattr(route, "methods", None) or {"GET"})
        for method in methods:
            if method in {"HEAD", "OPTIONS"}:
                continue
            classification = classify_route(method, path)
            entry = match_allowlist_entry(method, path)
            rows.append(
                {
                    "method": method,
                    "path": path,
                    "expected_auth_state": classification["expected_auth_state"],
                    "public_allowed": classification["public_allowed"],
                    "explicit_classification": classification["explicit_classification"],
                    "data_class": entry.data_class if entry else ("PRIVATE" if is_anonymous_denied(path) else "UNCLASSIFIED"),
                    "rate_limit": entry.rate_limit_per_min if entry else None,
                    "upstream_cost": entry.upstream_cost_budget if entry else None,
                    "licensing_status": entry.license_source_id if entry else None,
                    "cache_policy": entry.cache_policy if entry else "no-store",
                    "response_size_limit_kb": entry.response_size_limit_kb if entry else None,
                    "owner": entry.owner if entry else "unknown",
                    "test_evidence": entry.test_evidence if entry else None,
                }
            )
    rows.sort(key=lambda r: (r["path"], r["method"]))
    return rows


def probe_no_cookie_client(client: Any, rows: list[dict[str, Any]], *, limit: int = 120) -> list[dict[str, Any]]:
    probed: list[dict[str, Any]] = []
    for row in rows[:limit]:
        method = row["method"]
        path = row["path"]
        # Skip path templates with params for bulk probe.
        if "{" in path:
            probed.append({**row, "actual_no_cookie_response": "SKIPPED_TEMPLATE"})
            continue
        try:
            if method == "GET":
                resp = client.get(path, cookies={})
            elif method == "POST":
                resp = client.post(path, json={}, cookies={})
            else:
                resp = client.request(method, path, cookies={})
            actual = resp.status_code
        except Exception as exc:  # noqa: BLE001
            actual = f"ERROR:{type(exc).__name__}"
        expected = 200 if row["public_allowed"] else 401
        probed.append(
            {
                **row,
                "actual_no_cookie_response": actual,
                "expected_status_for_anonymous": expected,
                "probe_match": actual == expected or (row["public_allowed"] and actual in {200, 204, 302, 307}),
            }
        )
    return probed


def audit_route_inventory(app: Any, client: Any | None = None) -> dict[str, Any]:
    rows = scan_fastapi_routes(app)
    allowlist = allowlist_export()
    accidental: list[str] = []
    unclassified_public: list[str] = []
    for row in rows:
        key = f"{row['method']} {row['path']}"
        if row["public_allowed"] and not row["explicit_classification"] and row["path"].startswith("/api/"):
            unclassified_public.append(key)
        if (
            not row["public_allowed"]
            and not is_anonymous_denied(row["path"])
            and row["path"].startswith("/api/")
            and row["method"] == "GET"
            and "admin" not in row["path"]
            and row["data_class"] == "UNCLASSIFIED"
        ):
            # Potential accidental exposure if handler returns 200 without auth — flagged for probe.
            pass
        if is_anonymous_denied(row["path"]) and row.get("public_allowed"):
            accidental.append(key)
    probed = probe_no_cookie_client(client, rows) if client is not None else []
    leaks = [
        p["path"]
        for p in probed
        if p.get("actual_no_cookie_response") == 200
        and not p.get("public_allowed")
        and p["path"].startswith("/api/data-governance")
        or p["path"].startswith("/api/financial-data-security")
    ]
    return {
        "route_count": len(rows),
        "allowlist_count": len(allowlist),
        "routes": rows,
        "allowlist": allowlist,
        "probed_sample": probed[:40],
        "ACCIDENTAL_PUBLIC_ROUTES": accidental,
        "PUBLIC_ROUTES_WITHOUT_EXPLICIT_CLASSIFICATION": unclassified_public,
        "PRIVATE_DATA_EXPOSURE_PATHS": leaks,
    }
