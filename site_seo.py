"""Public SEO helpers — canonical URLs and document title constraints."""

from __future__ import annotations

import os
from typing import Any

# Paths that should canonicalize to a different public URL (no query strings).
CANONICAL_PATH_ALIASES: dict[str, str] = {
    "/oracle/accuracy": "/oracle-accuracy",
}


def public_site_origin() -> str:
    configured = (os.getenv("APP_BASE_URL") or "").strip().rstrip("/")
    return configured or "https://blackdark.io"


def canonical_path_for_request(path: str) -> str:
    p = path or "/"
    if not p.startswith("/"):
        p = "/" + p
    return CANONICAL_PATH_ALIASES.get(p, p)


def resolve_public_canonical_url(request: Any) -> str:
    """Absolute HTTPS canonical for the current HTML path."""
    path = canonical_path_for_request(getattr(getattr(request, "url", None), "path", None) or "/")
    return f"{public_site_origin()}{path}"
