"""Institutional gate verdict constants — isolated from 826 RTM classification namespace."""

from __future__ import annotations

# cap978 institutional closure gate success (NOT 826 RTM `classification` field).
INSTITUTIONAL_GATE_PASS = "INSTITUTIONAL_GATE_PASS"
INSTITUTIONAL_GATE_FAIL = "NOT_READY"

# Per-capability cap978 verify namespace (legacy; banned on cap646 RTM fields).
CAP978_VERIFY_VERDICT_COMPLETE = "VERIFIED_COMPLETE"
