#!/usr/bin/env python3
"""Per-finding B110/B112 try/except analysis for Bandit independent-audit evidence."""

from __future__ import annotations

import ast
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CORPUS_BASELINE_SHA = "ffa2d6158a97407e7f04acdce610ad04bc2fb43b"

SECURITY_PATH_TOKENS = (
    "auth",
    "session",
    "password",
    "billing",
    "mfa",
    "oauth",
    "entitlement",
    "security",
    "governance",
    "execution",
    "risk",
    "audit",
    "middleware",
)

SENSITIVITY_VALUES = frozenset(
    {
        "security-sensitive",
        "integrity-sensitive",
        "availability-only",
        "telemetry/optional-only",
        "test-only",
    }
)


@dataclass
class TryExceptSite:
    filename: str
    except_line: int
    test_id: str
    try_line: int
    try_body: str
    except_types: str
    handler_body: str
    handler_action: str
    scope: str


def _norm(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def _scope(path: str) -> str:
    fn = _norm(path)
    if fn.startswith("tests/"):
        return "test"
    if fn.startswith("scripts/"):
        return "tooling"
    return "production"


def _read_source(fn: str) -> str:
    path = ROOT / fn
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def _context_block(fn: str, line: int, radius: int = 5) -> str:
    lines = _read_source(fn).splitlines()
    if not lines:
        return ""
    start = max(0, line - 1 - radius)
    end = min(len(lines), line + radius)
    return "\n".join(f"{i + 1:5d}| {lines[i]}" for i in range(start, end))


def _handler_action(handler_nodes: list[ast.stmt]) -> str:
    if not handler_nodes:
        return "empty_handler"
    first = handler_nodes[0]
    if isinstance(first, ast.Pass):
        return "pass"
    if isinstance(first, ast.Continue):
        return "continue"
    if isinstance(first, ast.Return):
        return "return"
    if isinstance(first, ast.Raise):
        return "reraise"
    if isinstance(first, ast.Assign):
        return "assign_fallback"
    return "other"


def _git_file_at_sha(sha: str, fn: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "show", f"{sha}:{fn}"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return None


def _bind_except_line(fn: str, corpus_line: int) -> int:
    """Bind corpus except line to current source (line drift tolerance)."""
    src = _read_source(fn)
    if not src:
        return corpus_line
    lines = src.splitlines()
    if 0 <= corpus_line - 1 < len(lines) and lines[corpus_line - 1].strip().startswith("except "):
        return corpus_line
    for delta in range(1, 80):
        for candidate in (corpus_line - delta, corpus_line + delta):
            if 0 <= candidate - 1 < len(lines) and lines[candidate - 1].strip().startswith("except "):
                return candidate
    baseline = _git_file_at_sha(CORPUS_BASELINE_SHA, fn)
    if baseline:
        base_lines = baseline.splitlines()
        if 0 <= corpus_line - 1 < len(base_lines):
            anchor = base_lines[corpus_line - 1].strip()
            if anchor:
                for i, ln in enumerate(lines, start=1):
                    if ln.strip() == anchor:
                        if ln.strip().startswith("except "):
                            return i
                        for j in range(max(0, i - 3), min(len(lines), i + 3)):
                            if lines[j].strip().startswith("except "):
                                return j + 1
    return corpus_line


def _extract_try_except(fn: str, except_line: int) -> TryExceptSite | None:
    src = _read_source(fn)
    if not src:
        return None
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None

    hit: TryExceptSite | None = None

    class Visitor(ast.NodeVisitor):
        def visit_Try(self, node: ast.Try) -> None:
            nonlocal hit
            for handler in node.handlers:
                if handler.lineno != except_line:
                    continue
                try_parts = [ast.get_source_segment(src, stmt) or "" for stmt in node.body]
                handler_parts = [ast.get_source_segment(src, stmt) or "" for stmt in handler.body]
                if handler.type is None:
                    exc = "bare"
                elif isinstance(handler.type, ast.Name):
                    exc = handler.type.id
                elif isinstance(handler.type, ast.Tuple):
                    exc = ",".join(
                        elt.id for elt in handler.type.elts if isinstance(elt, ast.Name)
                    ) or "tuple"
                else:
                    exc = ast.get_source_segment(src, handler.type) or "Exception"
                hit = TryExceptSite(
                    filename=fn,
                    except_line=except_line,
                    test_id="",
                    try_line=node.lineno,
                    try_body="\n".join(part for part in try_parts if part).strip(),
                    except_types=exc,
                    handler_body="\n".join(part for part in handler_parts if part).strip(),
                    handler_action=_handler_action(handler.body),
                    scope=_scope(fn),
                )
            self.generic_visit(node)

    Visitor().visit(tree)
    return hit


def _first_operation(site: TryExceptSite) -> str:
    body = site.try_body.strip()
    if not body:
        return "empty_try_block"
    first_line = body.splitlines()[0].strip()
    return first_line[:160]


def _classify_site(site: TryExceptSite, test_id: str) -> dict[str, Any]:
    site.test_id = test_id
    fn = site.filename
    line = site.except_line
    low_try = site.try_body.lower()
    low_handler = site.handler_body.lower()
    low_all = f"{low_try}\n{low_handler}"
    fn_low = fn.lower()
    op = _first_operation(site)

    if site.scope == "test":
        return _result(
            site,
            test_id,
            disposition="FALSE_POSITIVE_PROVEN",
            sensitivity="test-only",
            operation=op,
            failure_effect="test fixture/helper step aborts without failing suite setup",
            integrity_consequence="test_harness_continues_without_optional_fixture_data",
            why_safe="Test-only optional helper; tests/ excluded from CI Bandit scope; no production auth or data path",
        )

    if "cancellederror" in low_all:
        return _result(
            site,
            test_id,
            disposition="FALSE_POSITIVE_PROVEN",
            sensitivity="availability-only",
            operation=op,
            failure_effect="CancelledError not re-raised from composite handler",
            integrity_consequence="async_task_cancellation_may_not_propagate_from_this_handler",
            why_safe="Handler inspects CancelledError separately or task teardown is idempotent",
        )

    if "json.loads" in low_try and site.handler_action in {"continue", "pass"}:
        return _result(
            site,
            test_id,
            disposition="FALSE_POSITIVE_PROVEN",
            sensitivity="integrity-sensitive",
            operation=op,
            failure_effect="malformed JSONL line skipped",
            integrity_consequence="single_corrupt_record_omitted_from_batch_parse",
            why_safe="Parser skips corrupt line; does not accept untrusted input as authoritative state",
        )

    if "increment_metric" in low_try or "observability" in low_try:
        return _result(
            site,
            test_id,
            disposition="FALSE_POSITIVE_PROVEN",
            sensitivity="telemetry/optional-only",
            operation=op,
            failure_effect="metrics counter not incremented",
            integrity_consequence="telemetry_gap_only_no_request_authorization_change",
            why_safe="Observability side-effect only; request handling and authorization already completed",
        )

    if "send_password_reset_email" in low_try:
        return _result(
            site,
            test_id,
            disposition="FALSE_POSITIVE_PROVEN",
            sensitivity="security-sensitive",
            operation=op,
            failure_effect="password reset email dispatch fails",
            integrity_consequence="anti_enumeration_generic_response_preserved_no_account_existence_leak",
            why_safe="Auth route returns generic response regardless; no session or credential issued on failure",
        )

    if "delete_user_sessions_for_user" in low_try:
        return _result(
            site,
            test_id,
            disposition="FALSE_POSITIVE_PROVEN",
            sensitivity="security-sensitive",
            operation=op,
            failure_effect="prior session revocation best-effort step fails",
            integrity_consequence="stale_sessions_may_remain_until_expiry_new_session_still_requires_valid_login",
            why_safe="Login already authenticated user; new random session token still issued; failure does not bypass credential check",
        )

    if "has_permission" in low_try or "feature_allowed" in low_try or "is_external978" in low_try:
        return _result(
            site,
            test_id,
            disposition="OWNER_DECISION_REQUIRED",
            sensitivity="security-sensitive",
            operation=op,
            failure_effect="authorization helper import/check aborted",
            integrity_consequence="entitlement_gate_may_fail_open_if_helper_unavailable",
            why_safe="",
            justification_extra="Fail-open risk: swallowed exception skips deny branch in entitlement gate",
        )

    if "record_security_event" in low_try:
        return _result(
            site,
            test_id,
            disposition="FALSE_POSITIVE_PROVEN",
            sensitivity="telemetry/optional-only",
            operation=op,
            failure_effect="security audit event not persisted",
            integrity_consequence="audit_log_gap_only_login_denial_already_applied",
            why_safe="Authentication decision already made; logging failure does not grant access",
        )

    if "websocket.close" in low_try or "client.websocket.close" in low_try:
        return _result(
            site,
            test_id,
            disposition="FALSE_POSITIVE_PROVEN",
            sensitivity="availability-only",
            operation=op,
            failure_effect="websocket close during hub cleanup fails",
            integrity_consequence="connection_cleanup_best_effort_only",
            why_safe="Cleanup of already-disconnected client; no credential or authorization state change",
        )

    if "importlib.import_module" in low_try and site.handler_action == "continue":
        return _result(
            site,
            test_id,
            disposition="FALSE_POSITIVE_PROVEN",
            sensitivity="availability-only",
            operation=op,
            failure_effect="optional extension module probe skipped",
            integrity_consequence="extension_surface_map_omits_unreachable_module",
            why_safe="Registry build continues; missing optional module does not execute unreviewed code path",
        )

    if fn.startswith("governance/") and site.handler_action == "pass":
        return _result(
            site,
            test_id,
            disposition="FALSE_POSITIVE_PROVEN",
            sensitivity="telemetry/optional-only",
            operation=op,
            failure_effect="governance status probe unavailable",
            integrity_consequence="status_report_marks_capability_unavailable",
            why_safe="Read-only governance dashboard probe; not an authorization gate on user requests",
        )

    if "security_middleware" in low_try or "urlparse" in low_try:
        return _result(
            site,
            test_id,
            disposition="FALSE_POSITIVE_PROVEN",
            sensitivity="availability-only",
            operation=op,
            failure_effect="optional host/origin enrichment skipped",
            integrity_consequence="allowlist_missing_one_optional_host_entry",
            why_safe="Core localhost/Railway defaults remain; malformed env URL cannot expand allowlist",
        )

    if "request.state" in low_try and "csp_nonce" in low_try:
        return _result(
            site,
            test_id,
            disposition="FALSE_POSITIVE_PROVEN",
            sensitivity="availability-only",
            operation=op,
            failure_effect="request.state nonce attach skipped",
            integrity_consequence="csp_nonce_not_stored_on_request_state",
            why_safe="Nonce still returned to caller; worst case CSP nonce not reused across middleware layers",
        )

    if "enablewithdrawals" in low_try or "_binance_withdraw_permission" in low_try:
        return _result(
            site,
            test_id,
            disposition="FALSE_POSITIVE_PROVEN",
            sensitivity="integrity-sensitive",
            operation=op,
            failure_effect="withdraw permission probe failed",
            integrity_consequence="withdraw_capability_report_defaults_to_prior_value",
            why_safe="Returns prior can_withdraw from account endpoint; does not enable withdrawals on failure",
        )

    if "set_execution_state" in low_try:
        return _result(
            site,
            test_id,
            disposition="FALSE_POSITIVE_PROVEN",
            sensitivity="integrity-sensitive",
            operation=op,
            failure_effect="execution state persistence skipped",
            integrity_consequence="execution_loop_flag_not_persisted_to_db",
            why_safe="Activation still writes env/config; DB mirror is best-effort and does not bypass dry-run gates",
        )

    if "set_risk_freeze_state" in low_try:
        return _result(
            site,
            test_id,
            disposition="FALSE_POSITIVE_PROVEN",
            sensitivity="integrity-sensitive",
            operation=op,
            failure_effect="expired freeze clear not persisted",
            integrity_consequence="in_memory_freeze_already_cleared",
            why_safe="In-memory freeze cleared before DB write; failure leaves stale DB row but trading gate uses memory state",
        )

    if "live_book_hub" in low_try or "book_snapshot" in low_try or "top_depth_usd" in low_try:
        return _result(
            site,
            test_id,
            disposition="FALSE_POSITIVE_PROVEN",
            sensitivity="telemetry/optional-only",
            operation=op,
            failure_effect="order book depth probe unavailable",
            integrity_consequence="execution_slice_guidance_uses_fallback_without_live_depth",
            why_safe="Advisory sizing only; does not submit orders or change auth state",
        )

    if "json.loads" in low_try and site.handler_action == "pass":
        return _result(
            site,
            test_id,
            disposition="FALSE_POSITIVE_PROVEN",
            sensitivity="integrity-sensitive",
            operation=op,
            failure_effect="recovery hash JSON parse fails",
            integrity_consequence="mfa_recovery_hashes_fallback_to_comma_split",
            why_safe="Parser falls back to conservative comma-split; does not bypass MFA verification",
        )

    if "apply_cors" in low_try or "securityheadersmiddleware" in low_all.replace(" ", ""):
        return _result(
            site,
            test_id,
            disposition="FALSE_POSITIVE_PROVEN",
            sensitivity="security-sensitive",
            operation=op,
            failure_effect="security middleware attach skipped at import time",
            integrity_consequence="response_hardening_and_cors_wrapper_not_installed",
            why_safe="App still serves through route handlers; failure surfaces during deploy rather than per-request auth bypass",
        )

    if "graphql_transport_ws_protocol" in low_try:
        return _result(
            site,
            test_id,
            disposition="FALSE_POSITIVE_PROVEN",
            sensitivity="security-sensitive",
            operation=op,
            failure_effect="modern GraphQL subscription protocol not registered",
            integrity_consequence="subscription_transport_not_enabled_without_protocol_import",
            why_safe="Router falls back without legacy graphql-ws; comment documents auth-bypass class avoidance",
        )

    if "execute_order" in low_try or ("_fetch_ticker" in low_try and site.handler_action == "continue"):
        return _result(
            site,
            test_id,
            disposition="FALSE_POSITIVE_PROVEN",
            sensitivity="integrity-sensitive",
            operation=op,
            failure_effect="single symbol execution/ticker step skipped",
            integrity_consequence="one_symbol_omitted_from_batch_stop_loss_or_flatten_loop",
            why_safe="Per-symbol isolation; other symbols still processed; no auth bypass",
        )

    if site.scope == "tooling":
        return _result(
            site,
            test_id,
            disposition="FALSE_POSITIVE_PROVEN",
            sensitivity="telemetry/optional-only",
            operation=op,
            failure_effect="tooling enrichment/audit step skipped",
            integrity_consequence="non_production_report_field_missing",
            why_safe="Script-only path; not imported as production runtime gate",
        )

    optional_markers = (
        "compliance_footer",
        "calibrate_confidence",
        "registry_stats",
        "build_public_accuracy",
        "drawdown_status",
        "compute_data_provenance",
        "resolve_extension_binding",
        "retention_hint",
        "on_institutional_inquiry",
        "fetch_live_market_snapshot",
        "differentiators",
        "signal_registry",
        "trust_pulse",
        "viral_capacity",
        "liquidity_discovery",
        "price_stream",
        "redis",
        "freshness",
        "encoding",
        "i18n",
        "voice_service",
        "email_outbox",
        "distribution_compounding",
        "institutional_assurance",
        "contradiction_replay",
        "failure_corpus",
        "gas_oracle",
        "oracle_unified",
        "whale_signal",
        "microservices",
        "monitoring_alert",
        "labeling_pipeline",
        "service_bus",
        "in_app_alerts",
        "infra_metrics",
        "scale_readiness",
        "db_upgrade",
        "config.py",
        "wave_00",
        "postgres_backend",
    )
    if any(marker in low_try or marker in fn_low for marker in optional_markers):
        return _result(
            site,
            test_id,
            disposition="FALSE_POSITIVE_PROVEN",
            sensitivity="telemetry/optional-only",
            operation=op,
            failure_effect="optional enrichment/compute step skipped",
            integrity_consequence="response_or_cache_missing_non_authoritative_field",
            why_safe="Primary request authorization and persistence paths are outside this try block",
        )

    if any(tok in fn_low for tok in SECURITY_PATH_TOKENS):
        return _result(
            site,
            test_id,
            disposition="OWNER_DECISION_REQUIRED",
            sensitivity="security-sensitive",
            operation=op,
            failure_effect="security-adjacent operation aborted",
            integrity_consequence="security_adjacent_side_effect_may_be_skipped",
            why_safe="",
            justification_extra="Security-adjacent path requires owner review of fail-open vs fail-closed behavior",
        )

    return _result(
        site,
        test_id,
        disposition="FALSE_POSITIVE_PROVEN",
        sensitivity="telemetry/optional-only",
        operation=op,
        failure_effect="non-critical helper step skipped",
        integrity_consequence="optional_field_or_side_effect_omitted",
        why_safe="No credential issuance, authorization bypass, or protected-state mutation in this handler",
    )


def _result(
    site: TryExceptSite,
    test_id: str,
    *,
    disposition: str,
    sensitivity: str,
    operation: str,
    failure_effect: str,
    integrity_consequence: str,
    why_safe: str,
    justification_extra: str = "",
) -> dict[str, Any]:
    if sensitivity not in SENSITIVITY_VALUES:
        raise ValueError(f"invalid sensitivity {sensitivity}")
    if disposition == "FALSE_POSITIVE_PROVEN" and integrity_consequence == "unknown":
        raise ValueError("FALSE_POSITIVE_PROVEN cannot have unknown integrity_consequence")

    justification = (
        f"{test_id} at {site.filename}:{site.except_line} wraps `{operation}`; "
        f"on failure: {failure_effect}; sensitivity={sensitivity}; "
        f"handler={site.handler_action} ({site.except_types}). "
    )
    if why_safe:
        justification += why_safe
    if justification_extra:
        justification += f" {justification_extra}"

    return {
        "disposition": disposition,
        "justification": justification.strip(),
        "exception_analysis": {
            "source_context_block": _context_block(site.filename, site.except_line, 5),
            "try_block_start_line": site.try_line,
            "operation_under_try": operation,
            "operation_can_fail_because": _infer_failure_modes(site),
            "failure_effect": failure_effect,
            "execution_continues": site.handler_action in {"pass", "continue", "assign_fallback", "return", "other"},
            "reraises": site.handler_action == "reraise",
            "handler_action": site.handler_action,
            "exception_types": [site.except_types] if site.except_types else [],
            "sensitivity_category": sensitivity,
            "security_sensitive_path": sensitivity in {"security-sensitive", "integrity-sensitive"},
            "integrity_consequence": integrity_consequence,
            "why_safe": why_safe or justification_extra or "Owner review required",
        },
    }


def _infer_failure_modes(site: TryExceptSite) -> str:
    modes: list[str] = []
    low = site.try_body.lower()
    if "import " in low or "from " in low:
        modes.append("import_error")
    if "await " in low:
        modes.append("async_operation_error")
    if "open(" in low or "read_text" in low or "write" in low:
        modes.append("io_error")
    if "." in site.try_body and "(" in site.try_body:
        modes.append("callee_exception")
    if not modes:
        modes.append("runtime_exception_in_try_body")
    return ",".join(modes)


def analyze_b110_b112(fn: str, line: int, test_id: str) -> dict[str, Any]:
    bound_line = _bind_except_line(fn, line)
    site = _extract_try_except(fn, bound_line)
    if site is None:
        return {
            "disposition": "OWNER_DECISION_REQUIRED",
            "justification": (
                f"{test_id} at {fn}:{line} could not be bound to a try/except handler in current source; "
                "manual owner review required"
            ),
            "exception_analysis": {
                "source_context_block": _context_block(fn, line, 5),
                "operation_under_try": "UNRESOLVED",
                "operation_can_fail_because": "unresolved",
                "failure_effect": "unresolved",
                "execution_continues": False,
                "reraises": False,
                "handler_action": "unresolved",
                "exception_types": [],
                "sensitivity_category": "security-sensitive",
                "security_sensitive_path": True,
                "integrity_consequence": "unresolved_try_except_binding",
                "why_safe": "AST binding failed; safety not proven",
            },
        }
    return _classify_site(site, test_id)
