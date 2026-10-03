"""Invoke semantic backend for dedicated batch wrappers (v6 §2.1 reuse + appropriateness)."""

from __future__ import annotations

from typing import Any


async def invoke_semantic_backend(capability_id: int, *, params: dict[str, Any]) -> dict[str, Any]:
    """Call semantic backend (not production spine) — avoids dedicated→production recursion."""
    from cap646.backend_executor import _call_entrypoint, _import_attr, _success_from_result
    from cap646.backend_registry import resolve_semantic_backend_binding

    binding = resolve_semantic_backend_binding(capability_id)
    fn = _import_attr(binding.module, binding.entrypoint)
    raw = await _call_entrypoint(fn, params=params, binding=binding)
    if not _success_from_result(raw):
        raise RuntimeError("semantic_backend_failed")
    result = {"success": True, "result": raw}
    if not result.get("success"):
        raise RuntimeError(str(result.get("error") or result.get("primary_error") or "backend_failed"))
    inner = result.get("result")
    if isinstance(inner, dict):
        return inner
    if isinstance(result, dict):
        return {k: v for k, v in result.items() if k not in {"compliance_footer", "evidence_metadata"}}
    return {"value": inner}
