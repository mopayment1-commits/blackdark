"""Financial-class-aware DLP and log sanitization (FDS-15 / SDG-10)."""

from __future__ import annotations

import re
from typing import Any

from financial_data.classification import FDSClass, classify_field, classify_payload, luhn_valid
from financial_data.sink_policy import PolicyViolation, Sink, enforce_sink_policy

_REDACTED = "[financial_redacted]"
_PAN_MASK_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
_CVV_CAPTURE_RE = re.compile(r"(?i)(\b(?:cvv|cvc|pin)\b\s*[:=]?\s*)(\d{3,4})\b")
_SECRET_RE = re.compile(
    r"(?i)(sk_live_[a-zA-Z0-9]{10,}|sk_test_[a-zA-Z0-9]{10,}|"
    r"AKIA[0-9A-Z]{16}|whsec_[a-zA-Z0-9]+|"
    r"postgres(ql)?://[^\s]+|redis://[^\s]+|"
    r"Bearer\s+[A-Za-z0-9._-]{10,})"
)
_IBAN_RE = re.compile(r"\b([A-Z]{2}\d{2}[A-Z0-9]{11,30})\b")


def _mask_pan_match(match: re.Match[str]) -> str:
    digits = re.sub(r"\D", "", match.group())
    if luhn_valid(digits):
        return _REDACTED
    return match.group()


def redact_financial_text(text: str) -> str:
    if not text:
        return text
    out = _SECRET_RE.sub(_REDACTED, text)
    out = _CVV_CAPTURE_RE.sub(lambda m: f"{m.group(1)}{_REDACTED}", out)
    out = _IBAN_RE.sub(_REDACTED, out)
    out = _PAN_MASK_RE.sub(_mask_pan_match, out)
    return out


def sanitize_financial_log_value(value: Any, *, field_name: str | None = None, max_len: int = 64) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    cls = classify_field(field_name, value)
    if cls in {FDSClass.C1_SAD, FDSClass.C2_PAN, FDSClass.C3_BANKING, FDSClass.C4_SECRET, FDSClass.UNKNOWN}:
        try:
            enforce_sink_policy(str(value), Sink.LOGS, field_hint=field_name)
        except PolicyViolation:
            return _REDACTED
    text = str(value).replace("\r", " ").replace("\n", " ")
    text = redact_financial_text(text)
    if cls in {FDSClass.C5_SENSITIVE_FINANCIAL, FDSClass.C6_PAYMENT_REFERENCE} and cls is not None:
        if len(text) > 8:
            text = f"{text[:4]}…{_REDACTED}"
    if len(text) > max_len:
        text = text[: max_len - 1] + "…"
    return text or "-"


def sanitize_financial_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    out: dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, dict):
            out[key] = sanitize_financial_payload(value)
        elif isinstance(value, list):
            out[key] = [
                sanitize_financial_payload(v) if isinstance(v, dict) else sanitize_financial_log_value(v, field_name=str(key))
                for v in value
            ]
        else:
            out[key] = sanitize_financial_log_value(value, field_name=str(key))
    return out


def scan_text_for_prohibited_patterns(text: str) -> list[dict[str, str]]:
    """Return sanitized findings — never echo prohibited values."""
    findings: list[dict[str, str]] = []
    for m in _SECRET_RE.finditer(text or ""):
        findings.append({"kind": "financial_secret", "offset": str(m.start())})
    for m in _CVV_CAPTURE_RE.finditer(text or ""):
        findings.append({"kind": "sad_cvv", "offset": str(m.start())})
    for m in _PAN_MASK_RE.finditer(text or ""):
        if luhn_valid(re.sub(r"\D", "", m.group())):
            findings.append({"kind": "luhn_pan", "offset": str(m.start()), "length": str(len(re.sub(r'\D', '', m.group())))})
    return findings


def assert_log_safe(value: Any, *, field_name: str | None = None) -> str:
    sanitized = sanitize_financial_log_value(value, field_name=field_name)
    if sanitized == _REDACTED and value not in (None, "", "-"):
        return sanitized
    return sanitized
