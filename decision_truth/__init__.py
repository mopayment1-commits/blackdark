"""BLACKDARK Decision Truth System — unified pipeline package (BGS-009)."""

from decision_truth.contract import DecisionContract, DecisionState
from decision_truth.pipeline import evaluate_opportunity, pipeline_status

__all__ = [
    "DecisionContract",
    "DecisionState",
    "evaluate_opportunity",
    "pipeline_status",
]
