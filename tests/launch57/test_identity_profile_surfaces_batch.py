"""Break tests — profile page must wire real identity APIs (no phantom UI)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / "templates" / "profile.html"

REQUIRED_API_PATHS = (
    "/api/auth/sessions",
    "/api/auth/secure-my-account",
    "/api/auth/login-history",
    "/api/privacy/dsr/status",
    "/api/privacy/dsr/export",
    "/api/privacy/dsr/erase",
    "/api/privileged/step-up",
)

REQUIRED_CONTROLS = (
    'id="sessionsList"',
    'id="loginHistoryList"',
    'data-bd-call="revokeOtherSessions"',
    'data-bd-call="exportMyData"',
    'data-bd-call="requestAccountDeletion"',
    'data-bd-call="revokeSession"',
    "method: 'DELETE'",
)

PHANTOM_MARKERS = (
    "mockFetch",
    "// TODO: wire",
    "fakeApi",
    "stubSession",
)


def test_profile_wires_identity_surface_apis():
    text = PROFILE.read_text(encoding="utf-8")
    for path in REQUIRED_API_PATHS:
        assert path in text, f"profile.html must call {path}"
    for marker in REQUIRED_CONTROLS:
        assert marker in text, f"profile.html missing control: {marker}"


def test_profile_has_no_phantom_identity_wiring():
    text = PROFILE.read_text(encoding="utf-8").lower()
    for bad in PHANTOM_MARKERS:
        assert bad.lower() not in text, f"phantom marker found: {bad}"


def test_profile_sessions_revoke_uses_delete_not_get():
    text = PROFILE.read_text(encoding="utf-8")
    assert "fetch('/api/auth/sessions/'" in text
    assert "method: 'DELETE'" in text
    assert "fetch('/api/auth/sessions'," in text
