"""Financial-class-aware DLP and log sanitization (FDS-15 / SDG-10)."""

from __future__ import annotations

import re
from typing import Any, Iterable

from financial_data.classification import FDSClass, classify_field, luhn_valid
from financial_data.sink_policy import PolicyViolation, Sink, enforce_sink_policy

_REDACTED = "[financial_redacted]"
_MAX_SCAN_LEN = 16_384

# Bounded, fixed-width secret prefixes — no unbounded `+` on user-controlled input.
_STRIPE_SK_RE = re.compile(r"sk_(?:live|test)_[A-Za-z0-9]{10,128}")
_AWS_KEY_RE = re.compile(r"AKIA[0-9A-Z]{16}")
_WHSEC_RE = re.compile(r"whsec_[A-Za-z0-9]{8,128}")
_PG_URL_RE = re.compile(r"postgres(?:ql)?://[^\s]{1,240}")
_REDIS_URL_RE = re.compile(r"redis://[^\s]{1,240}")
_BEARER_RE = re.compile(r"Bearer\s+[A-Za-z0-9._-]{10,256}")
_IBAN_RE = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b")

_CVV_KEYWORDS = ("cvv", "cvc", "pin")


def _bounded_scan_text(text: str) -> str:
    if len(text) <= _MAX_SCAN_LEN:
        return text
    return text[:_MAX_SCAN_LEN]


def _replace_spans(text: str, spans: Iterable[tuple[int, int]]) -> str:
    if not spans:
        return text
    merged: list[tuple[int, int]] = []
    for start, end in sorted(spans, key=lambda s: s[0]):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    out: list[str] = []
    cursor = 0
    for start, end in merged:
        out.append(text[cursor:start])
        out.append(_REDACTED)
        cursor = end
    out.append(text[cursor:])
    return "".join(out)


def _secret_pattern_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for pattern in (
        _STRIPE_SK_RE,
        _AWS_KEY_RE,
        _WHSEC_RE,
        _PG_URL_RE,
        _REDIS_URL_RE,
        _BEARER_RE,
    ):
        for match in pattern.finditer(text):
            spans.append((match.start(), match.end()))
    return spans


def _pan_candidate_spans(text: str) -> list[tuple[int, int]]:
    """Linear PAN scan — avoids nested-quantifier regex on full input."""
    spans: list[tuple[int, int]] = []
    i = 0
    length = len(text)
    while i < length:
        if not text[i].isdigit():
            i += 1
            continue
        start = i
        digits: list[str] = []
        j = i
        while j < length and len(digits) < 19:
            ch = text[j]
            if ch.isdigit():
                digits.append(ch)
                j += 1
            elif ch in " -" and j + 1 < length and text[j + 1].isdigit():
                j += 1
            else:
                break
        if 13 <= len(digits) <= 19 and luhn_valid("".join(digits)):
            spans.append((start, j))
        i = j if j > start else start + 1
    return spans


def _cvv_spans(text: str) -> list[tuple[int, int]]:
    """Redact digit runs after cvv/cvc/pin labels without polynomial regex."""
    lower = text.lower()
    spans: list[tuple[int, int]] = []
    for keyword in _CVV_KEYWORDS:
        search_from = 0
        while True:
            idx = lower.find(keyword, search_from)
            if idx < 0:
                break
            before_ok = idx == 0 or not lower[idx - 1].isalnum()
            after_kw = idx + len(keyword)
            after_ok = after_kw >= len(text) or not lower[after_kw].isalnum()
            if not (before_ok and after_ok):
                search_from = idx + 1
                continue
            j = after_kw
            while j < len(text) and text[j].isspace():
                j += 1
            if j < len(text) and text[j] in ":=":
                j += 1
                while j < len(text) and text[j].isspace():
                    j += 1
            digit_start = j
            digit_count = 0
            while j < len(text) and digit_count < 4 and text[j].isdigit():
                digit_count += 1
                j += 1
            if 3 <= digit_count <= 4:
                spans.append((digit_start, j))
            search_from = idx + 1
    return spans


def _iban_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for match in _IBAN_RE.finditer(text):
        spans.append((match.start(), match.end()))
    return spans


def redact_financial_text(text: str) -> str:
    if not text:
        return text
    bounded = _bounded_scan_text(text)
    spans: list[tuple[int, int]] = []
    spans.extend(_secret_pattern_spans(bounded))
    spans.extend(_cvv_spans(bounded))
    spans.extend(_iban_spans(bounded))
    spans.extend(_pan_candidate_spans(bounded))
    out = _replace_spans(bounded, spans)
    if len(text) > len(bounded):
        out += text[len(bounded) :]
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
    bounded = _bounded_scan_text(text or "")
    findings: list[dict[str, str]] = []
    for start, _end in _secret_pattern_spans(bounded):
        findings.append({"kind": "financial_secret", "offset": str(start)})
    for start, _end in _cvv_spans(bounded):
        findings.append({"kind": "sad_cvv", "offset": str(start)})
    for start, end in _pan_candidate_spans(bounded):
        findings.append(
            {
                "kind": "luhn_pan",
                "offset": str(start),
                "length": str(end - start),
            }
        )
    return findings


def assert_log_safe(value: Any, *, field_name: str | None = None) -> str:
    sanitized = sanitize_financial_log_value(value, field_name=field_name)
    if sanitized == _REDACTED and value not in (None, "", "-"):
        return sanitized
    return sanitized
