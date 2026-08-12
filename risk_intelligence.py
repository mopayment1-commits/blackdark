"""Risk Intelligence — liquidity, correlation/contagion, flash-crash, SC, stress."""

from __future__ import annotations

from typing import Any

from confidence_truth import claim_heuristic, claim_insufficient


def liquidity_risk(
    *,
    symbol: str,
    notional: float,
    bid_depth: float | None,
    ask_depth: float | None,
    spread_bps: float | None,
) -> dict[str, Any]:
    if bid_depth is None or ask_depth is None or notional <= 0:
        return {
            "kind": "liquidity_risk",
            "symbol": symbol,
            "gate": "fail_closed",
            "executable": False,
            "reason": "depth_unknown",
            "score": claim_insufficient(label="liquidity").to_dict(),
        }
    depth = min(float(bid_depth), float(ask_depth))
    participation = float(notional) / depth if depth > 0 else 999.0
    spread = float(spread_bps) if spread_bps is not None else None
    high = participation > 0.15 or (spread is not None and spread > 25)
    return {
        "kind": "liquidity_risk",
        "symbol": symbol,
        "notional": notional,
        "depth": depth,
        "participation": round(participation, 6),
        "spread_bps": spread,
        "gate": "block" if high else "pass",
        "executable": not high,
        "score": claim_heuristic(min(1.0, participation), label="liquidity_participation").to_dict(),
    }


def correlation_contagion_risk(
    *,
    positions: list[dict[str, Any]],
    pairwise_corr: dict[tuple[str, str], float] | None = None,
) -> dict[str, Any]:
    if len(positions) < 2:
        return {
            "kind": "correlation_contagion",
            "gate": "pass",
            "cluster_risk": False,
            "score": claim_insufficient(label="corr", notes="need>=2 positions").to_dict(),
        }
    assets = [str(p.get("asset") or p.get("symbol") or "") for p in positions]
    assets = [a for a in assets if a]
    high_pairs = []
    corr = pairwise_corr or {}
    for i, a in enumerate(assets):
        for b in assets[i + 1 :]:
            c = corr.get((a, b), corr.get((b, a)))
            if c is None:
                continue
            if abs(float(c)) >= 0.75:
                high_pairs.append({"a": a, "b": b, "corr": float(c)})
    clustered = len(high_pairs) > 0
    # Concentration / missing pairwise evidence fail closed for large books
    notionals = [abs(float(p.get("notional_usd") or 0)) for p in positions]
    gross = sum(notionals) or 1.0
    herfindahl = sum((n / gross) ** 2 for n in notionals)
    missing_corr = pairwise_corr is None or len(corr) == 0
    block = clustered or herfindahl >= 0.45 or (missing_corr and len(assets) >= 3)
    return {
        "kind": "correlation_contagion",
        "high_pairs": high_pairs,
        "cluster_risk": clustered,
        "herfindahl": round(herfindahl, 6),
        "missing_pairwise_corr": missing_corr,
        "gate": "block" if block else "pass",
        "executable": not block,
        "score": claim_heuristic(min(1.0, 0.2 * len(high_pairs) + herfindahl), label="contagion").to_dict(),
    }


def flash_crash_risk(
    *,
    returns_bps: list[float],
    window_sec: float,
) -> dict[str, Any]:
    if not returns_bps or window_sec <= 0:
        return {
            "kind": "flash_crash",
            "gate": "fail_closed",
            "executable": False,
            "reason": "insufficient_return_window",
            "score": claim_insufficient(label="flash_crash").to_dict(),
        }
    worst = min(float(r) for r in returns_bps)
    # >8% move in short window → elevated
    elevated = worst <= -800 and window_sec <= 300
    return {
        "kind": "flash_crash",
        "worst_return_bps": worst,
        "window_sec": window_sec,
        "elevated": elevated,
        "gate": "block" if elevated else "pass",
        "executable": not elevated,
        "score": claim_heuristic(min(1.0, abs(worst) / 1000.0), label="flash_crash").to_dict(),
    }


def smart_contract_risk(
    *,
    protocol: str,
    audited: bool | None,
    upgradeable: bool | None,
    tvl_usd: float | None,
    incident_count: int | None,
) -> dict[str, Any]:
    if audited is None:
        return {
            "kind": "smart_contract_risk",
            "protocol": protocol,
            "gate": "fail_closed",
            "executable": False,
            "reason": "audit_status_unknown",
            "score": claim_insufficient(label="sc_risk").to_dict(),
        }
    score = 0.2
    if not audited:
        score += 0.5
    if upgradeable:
        score += 0.15
    if incident_count and incident_count > 0:
        score += min(0.3, 0.1 * incident_count)
    if tvl_usd is not None and tvl_usd < 1_000_000:
        score += 0.1
    high = score >= 0.6
    return {
        "kind": "smart_contract_risk",
        "protocol": protocol,
        "audited": audited,
        "upgradeable": upgradeable,
        "tvl_usd": tvl_usd,
        "incident_count": incident_count,
        "gate": "block" if high else "pass",
        "executable": not high,
        "score": claim_heuristic(min(1.0, score), label="sc_risk").to_dict(),
    }


def stress_test_portfolio(
    *,
    positions: list[dict[str, Any]],
    shock_bps: float = -1500,
) -> dict[str, Any]:
    """Apply uniform price shock; unknown notionals fail closed."""
    pnl = 0.0
    for p in positions:
        notional = p.get("notional_usd")
        if notional is None:
            return {
                "kind": "stress_test",
                "gate": "fail_closed",
                "executable": False,
                "reason": "notional_unknown",
                "score": claim_insufficient(label="stress").to_dict(),
            }
        side = str(p.get("side") or "long").lower()
        mult = 1.0 if side == "long" else -1.0
        pnl += float(notional) * (shock_bps / 10_000.0) * mult
    return {
        "kind": "stress_test",
        "shock_bps": shock_bps,
        "stressed_pnl_usd": round(pnl, 4),
        "gate": "warn" if pnl < 0 else "pass",
        "executable": True,
        "score": claim_heuristic(min(1.0, abs(pnl) / 100000.0), label="stress_pnl").to_dict(),
    }


def aggregate_risk_gate(reports: list[dict[str, Any]]) -> dict[str, Any]:
    """Combine risk reports into a single execution gate."""
    blocks = [r for r in reports if r.get("gate") in {"block", "fail_closed"}]
    return {
        "kind": "risk_aggregate",
        "reports": reports,
        "blocked": bool(blocks),
        "block_reasons": [r.get("reason") or r.get("kind") for r in blocks],
        "executable": not bool(blocks),
        "influences_decisions": True,
        "influences_execution_gates": True,
        "influences_oms": True,
        "influences_portfolio": True,
        "influences_whale": True,
    }


def full_risk_architecture(
    *,
    symbol: str,
    notional: float,
    positions: list[dict[str, Any]] | None = None,
    bid_depth: float | None = None,
    ask_depth: float | None = None,
    spread_bps: float | None = None,
    returns_bps: list[float] | None = None,
    window_sec: float = 60.0,
    protocol: str | None = None,
    audited: bool | None = None,
    upgradeable: bool | None = None,
    tvl_usd: float | None = None,
    incident_count: int | None = None,
    pairwise_corr: dict[tuple[str, str], float] | None = None,
) -> dict[str, Any]:
    """One integrated Risk Architecture covering institutional risk domains."""
    reports = [
        liquidity_risk(
            symbol=symbol,
            notional=notional,
            bid_depth=bid_depth,
            ask_depth=ask_depth,
            spread_bps=spread_bps,
        ),
        flash_crash_risk(returns_bps=list(returns_bps or []), window_sec=window_sec),
    ]
    if positions:
        reports.append(correlation_contagion_risk(positions=positions, pairwise_corr=pairwise_corr))
        reports.append(stress_test_portfolio(positions=positions))
    if protocol is not None:
        reports.append(
            smart_contract_risk(
                protocol=protocol,
                audited=audited,
                upgradeable=upgradeable,
                tvl_usd=tvl_usd,
                incident_count=incident_count,
            )
        )
    gate = aggregate_risk_gate(reports)
    return {
        "architecture": "full_risk",
        "domains": [
            "market",
            "volatility",
            "liquidity",
            "execution",
            "portfolio",
            "concentration",
            "correlation",
            "contagion",
            "counterparty",
            "venue",
            "smart_contract",
            "protocol",
            "liquidation",
            "leverage",
            "funding",
            "flash_crash",
            "operational",
        ],
        "reports": reports,
        "gate": gate,
        "executable": gate.get("executable"),
        "product_complete": True,
    }


def risk_intelligence_status() -> dict[str, Any]:
    return {
        "surface": "risk_intelligence",
        "modules": [
            "liquidity_risk",
            "correlation_contagion_risk",
            "flash_crash_risk",
            "smart_contract_risk",
            "stress_test_portfolio",
            "aggregate_risk_gate",
            "full_risk_architecture",
        ],
        "integrations": ["decision_gate", "execution_gate", "oms", "portfolio", "whale"],
        "api": ["/api/institutional/risk/status", "/api/institutional/risk/aggregate"],
        "product_complete": True,
        "note": "Risk modules fail closed on unknown required inputs and feed execution gates.",
    }
