"""Official Playbook governance contract — spec §8 (AIE-010)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class PlaybookContract:
    playbook_id: str
    version: str
    purpose: str
    eligible_regimes: list[str] = field(default_factory=list)
    required_capabilities: list[str] = field(default_factory=list)
    optional_capabilities: list[str] = field(default_factory=list)
    dependence_model: str = "cluster_by_source_model"
    validation_state: str = "shadow"
    failure_abstention: list[str] = field(default_factory=list)
    expiry_at: str | None = None
    change_history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def validate_official(self) -> None:
        if self.validation_state not in {"replay", "walk_forward", "shadow", "verified"}:
            raise ValueError("official_playbook_requires_validation_state")
        if not self.purpose.strip():
            raise ValueError("playbook_purpose_required")


_REGISTRY: dict[str, PlaybookContract] = {}


def register_playbook(contract: PlaybookContract) -> PlaybookContract:
    contract.validate_official()
    _REGISTRY[contract.playbook_id] = contract
    return contract


def get_playbook(playbook_id: str) -> PlaybookContract | None:
    return _REGISTRY.get(playbook_id)


def list_playbooks() -> list[dict[str, Any]]:
    return [p.to_dict() for p in _REGISTRY.values()]


def _bootstrap_official_playbooks() -> None:
    if _REGISTRY:
        return
    register_playbook(
        PlaybookContract(
            playbook_id="official-risk-scan-v1",
            version="1.0.0",
            purpose="Scan portfolio risk with mandatory safety lenses",
            eligible_regimes=["intraday", "swing"],
            required_capabilities=["portfolio_ai"],
            optional_capabilities=["whale_signal_vs_noise"],
            validation_state="shadow",
            failure_abstention=["stale_data", "unresolved_conflict"],
            expiry_at="2027-01-01",
            change_history=[{"version": "1.0.0", "reason": "initial_shadow"}],
        )
    )


_bootstrap_official_playbooks()
