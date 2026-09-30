"""Sink policy matrix and enforcement for FDS-C1..C6."""

from __future__ import annotations

from enum import Enum
from typing import Any

from financial_data.classification import FDSClass, class_definition, classify_field, classify_payload


class Sink(str, Enum):
    LOGS = "logs"
    ANALYTICS = "analytics"
    AI_LLM = "ai_llm"
    SUPPORT_EXPORT = "support_export"
    STORAGE = "storage"
    BACKUPS = "backups"
    CACHE = "cache"
    CLIENT = "client"


class PolicyViolation(RuntimeError):
    def __init__(self, *, sink: Sink, classification: FDSClass, field: str | None = None, reason: str = ""):
        self.sink = sink
        self.classification = classification
        self.field = field
        self.reason = reason
        super().__init__(reason or f"sink_policy_violation:{sink.value}:{classification.value}")


def policy_matrix() -> dict[str, dict[str, Any]]:
    return {
        cls.value: {
            "prohibited_sinks": sorted(class_definition(cls).prohibited_sinks),
            "logging_policy": class_definition(cls).logging_policy,
            "analytics_policy": class_definition(cls).analytics_policy,
            "ai_llm_policy": class_definition(cls).ai_llm_policy,
            "storage_policy": class_definition(cls).storage_policy,
            "masking_required": class_definition(cls).masking_required,
            "policy_version": class_definition(cls).reason,
        }
        for cls in FDSClass
        if cls != FDSClass.UNKNOWN
    }


def is_sink_allowed(
    classification: FDSClass,
    sink: Sink | str,
    *,
    purpose: str | None = None,
) -> bool:
    sink_name = sink.value if isinstance(sink, Sink) else str(sink)
    policy = class_definition(classification)
    if sink_name in policy.prohibited_sinks:
        return False
    if classification == FDSClass.UNKNOWN:
        return False
    if purpose and purpose not in policy.allowed_purposes and classification in {
        FDSClass.C5_SENSITIVE_FINANCIAL,
        FDSClass.C6_PAYMENT_REFERENCE,
    }:
        return purpose in {"authorized_operations", "billing_operations", "support_with_auth", "minimized_analytics", "aggregate_only"}
    if classification in {FDSClass.C5_SENSITIVE_FINANCIAL, FDSClass.C6_PAYMENT_REFERENCE}:
        if sink_name == Sink.AI_LLM.value:
            return False
    return True


def enforce_sink_policy(
    payload: dict[str, Any] | str | None,
    sink: Sink,
    *,
    purpose: str | None = None,
    field_hint: str | None = None,
) -> None:
    if payload is None:
        return
    if isinstance(payload, str):
        cls = classify_field(field_hint, payload)
        if not is_sink_allowed(cls, sink, purpose=purpose):
            raise PolicyViolation(sink=sink, classification=cls, field=field_hint, reason=class_definition(cls).reason)
        return
    mapping = classify_payload(payload if isinstance(payload, dict) else {})
    for path, cls in mapping.items():
        if not is_sink_allowed(cls, sink, purpose=purpose):
            raise PolicyViolation(sink=sink, classification=cls, field=path, reason=class_definition(cls).reason)
