"""Google OAuth live IdP drill: secret-free receipts; FAIL closed without live Google."""

from __future__ import annotations

import json


FAKE_CLIENT_ID = "blackdark-test-google-client-id.example.invalid"
FAKE_SECRET = "blackdark-test-oauth-client-secret"
FAKE_BASE = "https://staging.example.test"


class _Resp:
    def __init__(self, status: int, url: str, text: str = "", json_body=None):
        self.status_code = status
        self.url = url
        self.text = text
        self._json = json_body if json_body is not None else {}

    def json(self):
        return self._json


def _env(monkeypatch, tmp_path):
    monkeypatch.setenv("OAUTH_GOOGLE_EVIDENCE_PATH", str(tmp_path / "oauth.json"))
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_ID", FAKE_CLIENT_ID)
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_SECRET", FAKE_SECRET)
    monkeypatch.setenv("APP_BASE_URL", FAKE_BASE)


def test_oauth_idp_fail_closed_without_secrets(monkeypatch, tmp_path):
    monkeypatch.setenv("OAUTH_GOOGLE_EVIDENCE_PATH", str(tmp_path / "oauth.json"))
    monkeypatch.delenv("OAUTH_GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("OAUTH_GOOGLE_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("APP_BASE_URL", raising=False)
    from launch_drills import drill_oauth_google_idp

    row = drill_oauth_google_idp()
    assert row["id"] == "oauth_google_idp"
    assert row["verdict"] == "FAIL"
    assert row["verdict"] != "NOT_TESTED"
    assert row["reason"] == "secrets_missing"
    blob = json.dumps(row)
    assert "GOCSPX" not in blob
    stamped = json.loads((tmp_path / "oauth.json").read_text(encoding="utf-8"))
    assert stamped["verdict"] == "FAIL"
    assert stamped["human_callback_completed"] is False


def test_oauth_idp_requires_app_base_url(monkeypatch, tmp_path):
    monkeypatch.setenv("OAUTH_GOOGLE_EVIDENCE_PATH", str(tmp_path / "oauth.json"))
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_ID", FAKE_CLIENT_ID)
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_SECRET", FAKE_SECRET)
    monkeypatch.delenv("APP_BASE_URL", raising=False)
    from oauth_service import prove_google_oauth_idp

    receipt = prove_google_oauth_idp()
    assert receipt["ok"] is False
    assert receipt["reason"] == "app_base_url_missing"
    assert FAKE_SECRET not in json.dumps(receipt)
    assert FAKE_CLIENT_ID not in json.dumps(receipt)


def test_oauth_idp_redirect_uri_mismatch(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)

    class _Client:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get(self, url, **k):
            return _Resp(
                400,
                "https://accounts.google.com/signin/oauth/error?error=redirect_uri_mismatch",
                "Error 400: redirect_uri_mismatch",
            )

        def post(self, url, data=None, **k):
            return _Resp(400, url, "", {"error": "invalid_grant"})

    import httpx

    monkeypatch.setattr(httpx, "Client", _Client)
    from oauth_service import prove_google_oauth_idp

    receipt = prove_google_oauth_idp()
    assert receipt["ok"] is False
    assert receipt["reason"] == "redirect_uri_mismatch"
    assert receipt["authorize_accepted"] is False
    assert FAKE_SECRET not in json.dumps(receipt)


def test_oauth_idp_invalid_client_secret(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)

    class _Client:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get(self, url, **k):
            return _Resp(
                200,
                "https://accounts.google.com/o/oauth2/v2/auth",
                "<html>Google Sign in identifierId</html>",
            )

        def post(self, url, data=None, **k):
            return _Resp(401, url, "", {"error": "invalid_client"})

    import httpx

    monkeypatch.setattr(httpx, "Client", _Client)
    from oauth_service import prove_google_oauth_idp

    receipt = prove_google_oauth_idp()
    assert receipt["ok"] is False
    assert receipt["reason"] == "invalid_client"
    assert receipt["authorize_accepted"] is True
    assert receipt["token_client_accepted"] is False


def test_oauth_idp_pass_on_mocked_google(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)

    class _Client:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get(self, url, **k):
            from urllib.parse import unquote

            decoded = unquote(url)
            assert "response_type=code" in decoded
            assert "/api/auth/oauth/google/callback" in decoded
            return _Resp(
                200,
                "https://accounts.google.com/v3/signin/identifier",
                "<html>Sign in to continue to BLACKDARK identifierId</html>",
            )

        def post(self, url, data=None, **k):
            assert data["grant_type"] == "authorization_code"
            assert data["redirect_uri"].endswith("/api/auth/oauth/google/callback")
            return _Resp(400, url, "", {"error": "invalid_grant", "error_description": "Malformed auth code."})

    import httpx

    monkeypatch.setattr(httpx, "Client", _Client)
    from launch_drills import drill_oauth_google_idp
    from oauth_service import oauth_google_live_proved

    row = drill_oauth_google_idp()
    assert row["verdict"] == "PASS", row
    assert row["start_ok"] is True
    assert row["authorize_accepted"] is True
    assert row["token_client_accepted"] is True
    assert row["human_callback_completed"] is False
    assert row["redirect_uri"] == f"{FAKE_BASE}/api/auth/oauth/google/callback"
    blob = json.dumps(row)
    assert FAKE_SECRET not in blob
    assert FAKE_CLIENT_ID not in blob
    assert oauth_google_live_proved() is True
    stamped = json.loads((tmp_path / "oauth.json").read_text(encoding="utf-8"))
    assert stamped["verdict"] == "PASS"
    assert stamped["path"] == "oauth_service.prove_google_oauth_idp"
