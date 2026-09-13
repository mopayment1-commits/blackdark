"""Typed Capability Graph — spec §18 (AIE-011). CAUSES forbidden without contract."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class EdgeType(str, Enum):
    DATA_FEEDS = "DATA_FEEDS"
    DERIVED_FROM = "DERIVED_FROM"
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    USED_BY = "USED_BY"
    CANONICAL_REUSE = "CANONICAL_REUSE"
    EVIDENCE_FOR = "EVIDENCE_FOR"
    CAUSES = "CAUSES"


class GraphEdge(BaseModel):
    source_id: str
    target_id: str
    edge_type: EdgeType
    causal_evidence_contract: str | None = None

    @field_validator("edge_type")
    @classmethod
    def _validate_causes(cls, v: EdgeType, info):  # noqa: ANN001
        return v

    def model_post_init(self, __context: Any) -> None:  # noqa: ANN401
        if self.edge_type == EdgeType.CAUSES and not (self.causal_evidence_contract or "").strip():
            raise ValueError("causes_edge_requires_causal_evidence_contract")


def validate_edge(edge: dict[str, Any]) -> GraphEdge:
    return GraphEdge(**edge)


def add_edge(store: list[dict[str, Any]], edge: dict[str, Any]) -> dict[str, Any]:
    row = validate_edge(edge).model_dump()
    store.append(row)
    return row
