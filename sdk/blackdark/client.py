"""Minimal official client for Trust OS public/decision APIs."""

from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None  # type: ignore


class BlackdarkClient:
    """Semver-stable SDK surface for institutional integrators."""

    def __init__(self, base_url: str = "http://127.0.0.1:8080", *, token: str | None = None, timeout: float = 20.0):
        self.base_url = base_url.rstrip("/") + "/"
        self.token = token
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        h = {"Accept": "application/json", "User-Agent": "blackdark-sdk/1.0.0"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if httpx is None:
            raise RuntimeError("httpx required for blackdark SDK")
        url = urljoin(self.base_url, path.lstrip("/"))
        r = httpx.get(url, params=params, headers=self._headers(), timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def trust_pulse(self, symbol: str = "BTC") -> dict[str, Any]:
        return self._get("/api/trust-pulse", {"symbol": symbol})

    def coverage_honesty(self) -> dict[str, Any]:
        return self._get("/api/public/coverage-honesty")

    def model_card(self) -> dict[str, Any]:
        return self._get("/api/institutional/model-card")

    def dd_closure(self) -> dict[str, Any]:
        return self._get("/api/institutional/dd-closure")

    def kill_rate(self) -> dict[str, Any]:
        return self._get("/api/public/kill-rate")
