"""Reproducibility manifest for material replay/evaluation runs (P2)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping

from blackdark.temporal.replay import ReplayResult


@dataclass(frozen=True, slots=True)
class ReproducibilityManifest:
    """TEMP-AR-0324..0337."""

    code_sha: str | None
    configuration: Mapping[str, Any]
    dataset_snapshot: Mapping[str, Any]
    feature_version: str | None
    model_version: str | None
    rule_version: str | None
    evaluator_version: str | None
    random_seed: str | None
    environment: str | None
    run_id: str
    timestamps: Mapping[str, Any]
    evidence_class: str
    full_reproducibility_possible: bool
    reproducibility_limitations: tuple[str, ...] = field(default_factory=tuple)

    def to_metadata(self) -> dict[str, Any]:
        return {
            "code_sha": self.code_sha,
            "configuration": dict(self.configuration),
            "dataset_snapshot": dict(self.dataset_snapshot),
            "feature_version": self.feature_version,
            "model_version": self.model_version,
            "rule_version": self.rule_version,
            "evaluator_version": self.evaluator_version,
            "random_seed": self.random_seed,
            "environment": self.environment,
            "run_id": self.run_id,
            "timestamps": dict(self.timestamps),
            "evidence_class": self.evidence_class,
            "full_reproducibility_possible": self.full_reproducibility_possible,
            "reproducibility_limitations": list(self.reproducibility_limitations),
        }


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def build_reproducibility_manifest(
    replay_result: ReplayResult,
    *,
    code_sha: str | None = None,
    model_version: str | None = None,
    evaluator_version: str | None = None,
    environment: str = "deterministic_test",
    random_seed: str = "fixed",
) -> ReproducibilityManifest:
    manifest = replay_result.replay_manifest
    dataset_snapshot = {
        "input_event_identity_set": manifest.get("input_event_identity_set"),
        "source_versions": manifest.get("source_versions"),
        "dataset_versions": manifest.get("dataset_versions"),
    }
    limitations: list[str] = []
    full_repro = replay_result.success
    if not replay_result.success:
        limitations.append("replay_not_fully_successful")
        full_repro = False

    return ReproducibilityManifest(
        code_sha=code_sha or hashlib.sha256(b"p2-deterministic").hexdigest(),
        configuration=dict(manifest.get("replay_parameters", {})),
        dataset_snapshot=dataset_snapshot,
        feature_version=manifest.get("engine_version_or_contract_version"),
        model_version=model_version,
        rule_version=manifest.get("engine_version_or_contract_version"),
        evaluator_version=evaluator_version,
        random_seed=random_seed,
        environment=environment,
        run_id=replay_result.replay_id,
        timestamps={
            "start_time": manifest.get("start_time"),
            "end_time": manifest.get("end_time"),
            "simulated_time_sequence": manifest.get("simulated_time_sequence"),
        },
        evidence_class=replay_result.evidence_class,
        full_reproducibility_possible=full_repro,
        reproducibility_limitations=tuple(limitations),
    )
