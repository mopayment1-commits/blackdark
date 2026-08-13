"""Minimal official client for Trust OS public/decision APIs."""

from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None  # type: ignore


class BlackdarkClient:
    """Semver-stable SDK surface for institutional integrators.

    Prefer ``api_key`` (Decision API v1). Session ``token`` remains for
    Trust OS product routes and is not a commercial API credential.
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8080",
        *,
        token: str | None = None,
        api_key: str | None = None,
        timeout: float = 20.0,
    ):
        self.base_url = base_url.rstrip("/") + "/"
        self.token = token
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        h = {"Accept": "application/json", "User-Agent": "blackdark-sdk/1.1.0"}
        if self.api_key:
            h["X-API-Key"] = self.api_key
            h["Authorization"] = f"Bearer {self.api_key}"
        elif self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if httpx is None:
            raise RuntimeError("httpx required for blackdark SDK")
        url = urljoin(self.base_url, path.lstrip("/"))
        r = httpx.get(url, params=params, headers=self._headers(), timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def _post(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        if httpx is None:
            raise RuntimeError("httpx required for blackdark SDK")
        url = urljoin(self.base_url, path.lstrip("/"))
        r = httpx.post(url, json=json or {}, headers=self._headers(), timeout=self.timeout)
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

    def oracle(self, symbol: str = "BTC") -> dict[str, Any]:
        return self._get(f"/api/v1/oracle/{symbol}")

    def decision_certificate(self, symbol: str = "BTC") -> dict[str, Any]:
        return self._post(f"/api/v1/oracle/{symbol}/certificate")

    def accuracy(self) -> dict[str, Any]:
        return self._get("/api/v1/accuracy")

    def feed(self, limit: int | None = None) -> dict[str, Any]:
        params = {"limit": limit} if limit is not None else None
        return self._get("/api/v1/feed", params)

    def me(self) -> dict[str, Any]:
        return self._get("/api/v1/me")
