"""BLACKDARK financial data security — classification, DLP, scanning, boundaries."""

from financial_data.classification import (
    CLASS_POLICY_VERSION,
    FDSClass,
    classify_field,
    classify_payload,
    class_definition,
)
from financial_data.boundary import (
    gate_analytics_export,
    gate_external_llm_payload,
    gate_support_export,
    prepare_llm_context,
)
from financial_data.dlp import sanitize_financial_log_value, sanitize_financial_payload
from financial_data.sink_policy import Sink, is_sink_allowed, policy_matrix

__all__ = [
    "CLASS_POLICY_VERSION",
    "FDSClass",
    "Sink",
    "class_definition",
    "classify_field",
    "classify_payload",
    "gate_analytics_export",
    "gate_external_llm_payload",
    "gate_support_export",
    "is_sink_allowed",
    "policy_matrix",
    "prepare_llm_context",
    "sanitize_financial_log_value",
    "sanitize_financial_payload",
]
