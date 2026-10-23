"""Input normalization — XSS-oriented stripping for plain-text fields."""

from __future__ import annotations

import html
import re
from typing import Any

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_SCRIPTISH = re.compile(r"(?is)<\s*/?\s*script\b[^>]*>|javascript\s*:")


def sanitize_plain_text(value: Any, *, max_len: int = 10_000) -> str:
    text = html.unescape(str(value or ""))
    text = _CONTROL.sub("", text)
    text = _SCRIPTISH.sub("", text)
    text = text.strip()
    if len(text) > max_len:
        text = text[:max_len]
    return text


def sanitize_email_local_part(value: str) -> str:
    return sanitize_plain_text(value, max_len=320).lower()
