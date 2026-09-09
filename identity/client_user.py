"""Client-safe user serialization — hide sequential internal ids."""

from __future__ import annotations

from typing import Any


def serialize_user_for_client(user: dict[str, Any]) -> dict[str, Any]:
    public_id = str(user.get("public_user_id") or "")
    payload = {k: v for k, v in user.items() if k != "id"}
    payload["public_user_id"] = public_id
    return payload
