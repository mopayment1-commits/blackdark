"""FastAPI route inventory + no-cookie probe helpers — AV §17."""

from __future__ import annotations

from typing import Any

from anonymous_visitor.allowlist import allowlist_export, is_anonymous_allowed, is_anonymous_denied, match_allowlist_entry
from anonymous_visitor.registry import classify_route


def _route_data_class(method: str, path: str, entry: Any | None) -> str:
    if entry is not None:
        return entry.data_class
    if is_anonymous_denied(path):
        return "PRIVATE"
    if not is_anonymous_allowed(method, path):
        return "PRIVATE"
    if method.upper() == "GET" and not path.startswith("/api/"):
        return "PUBLIC_MARKETING"
    if path.startswith("/api/auth/"):
        return "PUBLIC_UTILITY"
    return "UNCLASSIFIED"


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
                    "data_class": _route_data_class(method, path, entry),
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


def summarize_route_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "TOTAL_ROUTES_DISCOVERED": len(rows),
        "TOTAL_PUBLIC": sum(1 for r in rows if r["public_allowed"]),
        "TOTAL_PRIVATE": sum(1 for r in rows if not r["public_allowed"]),
        "TOTAL_AUTHENTICATED": sum(
            1 for r in rows if r["expected_auth_state"] == "AUTHENTICATED" and not r["public_allowed"]
        ),
        "TOTAL_ADMIN": sum(1 for r in rows if "/admin" in r["path"]),
        "TOTAL_INTERNAL": sum(1 for r in rows if r["path"].startswith("/metrics") or "/internal" in r["path"]),
        "TOTAL_UNCLASSIFIED": sum(1 for r in rows if r["data_class"] == "UNCLASSIFIED"),
    }


def probe_no_cookie_client(client: Any, rows: list[dict[str, Any]], *, limit: int = 120) -> list[dict[str, Any]]:
    skip_prefixes = ("/api/trust-pulse/stream", "/metrics", "/webhook/")
    probed: list[dict[str, Any]] = []
    count = 0
    for row in rows:
        if count >= limit:
            break
        method = row["method"]
        path = row["path"]
        if any(path.startswith(p) for p in skip_prefixes):
            continue
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
        count += 1
    return probed


def audit_route_inventory(app: Any, client: Any | None = None) -> dict[str, Any]:
    rows = scan_fastapi_routes(app)
    allowlist = allowlist_export()
    counts = summarize_route_counts(rows)
    accidental: list[str] = []
    unclassified_public: list[str] = []
    unclassified_routes: list[str] = []
    for row in rows:
        key = f"{row['method']} {row['path']}"
        if row["data_class"] == "UNCLASSIFIED":
            unclassified_routes.append(key)
        if row["public_allowed"] and not row["explicit_classification"] and row["path"].startswith("/api/"):
            unclassified_public.append(key)
        if (
            not row["public_allowed"]
            and not is_anonymous_denied(row["path"])
            and row["path"].startswith("/api/")
            and row["method"] == "GET"
            and "admin" not in row["path"]
            and row.get("actual_no_cookie_response") == 200
        ):
            accidental.append(key)
        if is_anonymous_denied(row["path"]) and row.get("public_allowed"):
            accidental.append(key)
    probed = probe_no_cookie_client(client, rows) if client is not None else []
    if probed:
        for row in probed:
            key = f"{row['method']} {row['path']}"
            if (
                row.get("actual_no_cookie_response") == 200
                and not row.get("public_allowed")
                and row["path"].startswith("/api/")
                and not is_anonymous_denied(row["path"])
            ):
                if key not in accidental:
                    accidental.append(key)
    leaks = [
        p["path"]
        for p in probed
        if p.get("actual_no_cookie_response") == 200
        and not p.get("public_allowed")
        and (
            p["path"].startswith("/api/data-governance")
            or p["path"].startswith("/api/financial-data-security")
        )
    ]
    return {
        **counts,
        "route_count": len(rows),
        "allowlist_count": len(allowlist),
        "routes": rows,
        "allowlist": allowlist,
        "probed_sample": probed[:40],
        "UNCLASSIFIED_ROUTES": unclassified_routes,
        "ACCIDENTAL_PUBLIC_ROUTES": accidental,
        "PUBLIC_ROUTES_WITHOUT_EXPLICIT_CLASSIFICATION": unclassified_public,
        "PRIVATE_DATA_EXPOSURE_PATHS": leaks,
    }


def sanitized_route_inventory_summary(app: Any) -> dict[str, Any]:
    rows = scan_fastapi_routes(app)
    counts = summarize_route_counts(rows)
    return {
        "ok": True,
        "sanitized": True,
        "full_inventory_requires_auth": True,
        **counts,
    }
