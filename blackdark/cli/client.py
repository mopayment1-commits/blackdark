"""REST API client for BLACKDARK CLI — Feature #167."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from blackdark.cli.errors import exit_code_for_http

_DEFAULT_BASE = os.getenv("BLACKDARK_API_URL", "http://127.0.0.1:8000").rstrip("/")
EXIT_ERROR = 1


class CliApiError(Exception):
    def __init__(self, message: str, *, status: int = 0, exit_code: int = EXIT_ERROR, body: Any = None):
        super().__init__(message)
        self.status = status
        self.exit_code = exit_code
        self.body = body


class BlackdarkApiClient:
    """Thin wrapper around Unified REST API (#162)."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        bearer_token: str | None = None,
        timeout_sec: float = 15.0,
    ):
        self.base_url = (base_url or _DEFAULT_BASE).rstrip("/")
        self.api_key = (api_key or os.getenv("BLACKDARK_API_KEY") or os.getenv("X_API_KEY") or "").strip()
        self.bearer_token = (bearer_token or os.getenv("BLACKDARK_TOKEN") or "").strip()
        self.timeout_sec = timeout_sec

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json", "User-Agent": "blackdark-cli/1.0"}
        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        if params:
            query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
            url = f"{url}?{query}"

        data = None
        headers = self._headers()
        if json_body is not None:
            data = json.dumps(json_body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                raw = resp.read().decode("utf-8")
                if not raw.strip():
                    return {"ok": True}
                return json.loads(raw)
        except urllib.error.HTTPError as exc:
            body: Any = None
            try:
                body = json.loads(exc.read().decode("utf-8"))
            except Exception:
                body = None
            detail = body.get("detail") if isinstance(body, dict) else str(exc.reason)
            raise CliApiError(
                str(detail or exc.reason),
                status=exc.code,
                exit_code=exit_code_for_http(exc.code),
                body=body,
            ) from exc
        except urllib.error.URLError as exc:
            raise CliApiError(f"Connection failed: {exc.reason}", exit_code=EXIT_ERROR) from exc
        except json.JSONDecodeError as exc:
            raise CliApiError("Invalid JSON response from API", exit_code=EXIT_ERROR) from exc

    def get(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.request("GET", path, params=params)

    def post(self, path: str, *, json_body: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.request("POST", path, json_body=json_body)
