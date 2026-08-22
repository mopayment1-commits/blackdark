"""User-surface validation rules — /cap646 hub alone is never sufficient for closure."""

from __future__ import annotations

from cap646.ui_pages import USER_SURFACES, user_surface_for
from cap646.waves import USER_FACING

# Paths that count as dedicated product surfaces (not generic capability hub)
DEDICATED_UI_PATHS = frozenset(
    {
        "/dashboard",
        "/institutional",
        "/oracle-accuracy",
        "/trust-pulse",
        "/data-room",
        "/portfolio",
        "/alerts",
        "/ai-chat",
        "/b2b",
        "/unique/ten",
    }
)

# Infrastructure capabilities may use /cap646 but must prove operational outcome
INFRA_HUB_CAPABILITIES = frozenset({507, 534, 631, 630, 338, 500})


def dedicated_surface_for(capability_id: int) -> dict[str, str] | None:
    return USER_SURFACES.get(capability_id) or user_surface_for(capability_id)


def has_dedicated_user_surface(capability_id: int) -> bool:
    """True when capability maps to a product journey surface, not hub-only."""
    if capability_id not in USER_FACING:
        return True  # not required
    surf = dedicated_surface_for(capability_id)
    if not surf:
        return False
    ui_path = surf.get("ui_path", "")
    if ui_path in DEDICATED_UI_PATHS:
        return True
    if capability_id in INFRA_HUB_CAPABILITIES:
        # Infra may use hub but requires operational validation separately
        return False
    return ui_path != "/cap646"


def hub_only_surface(capability_id: int) -> bool:
    if capability_id not in USER_FACING:
        return False
    surf = dedicated_surface_for(capability_id)
    if not surf:
        return True
    return surf.get("ui_path") == "/cap646" and capability_id not in INFRA_HUB_CAPABILITIES


def surface_evidence(capability_id: int) -> list[str]:
    surf = dedicated_surface_for(capability_id)
    if not surf:
        return []
    return [f"ui_path={surf.get('ui_path')}", f"api_path={surf.get('api_path')}", f"label={surf.get('label')}"]
