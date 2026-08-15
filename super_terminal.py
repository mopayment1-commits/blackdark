"""Super Terminal — institutional multi-module surface with real backends."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def _derivatives_pack(symbol: str) -> dict[str, Any]:
    """Spot-futures / funding pack via Canonical Truth Bus venue L2 + venue funding.

    Requires venue perpetual books and venue funding rates. Does not derive perp from spot
    and does not inject constant funding rates.
    """
    from arbitrage_engine import calculate_funding_arbitrage, calculate_spot_futures_premium
    from canonical_truth_bus import get_live_books, get_live_funding

    try:
        live_books = get_live_books(require_live=True, symbol=symbol)
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "source": "canonical_truth_bus",
            "symbol": symbol,
            "reason": f"live_books_unavailable:{type(exc).__name__}",
            "book_source": "unavailable",
            "live_anchored": False,
            "computed": False,
            "synthetic_forbidden": True,
        }

    books: dict[str, dict[str, dict[str, Any]]] = {}
    perp_venues: list[str] = []
    for venue, symbols in live_books.items():
        spot = symbols.get(symbol)
        perp = symbols.get(f"{symbol}@perpetual")
        if not spot or not perp:
            continue
        if spot.get("fabricated_depth") or perp.get("fabricated_depth"):
            continue
        if perp.get("depth_source") != "venue_l2":
            continue
        books[venue] = {
            symbol: {**spot, "venue": venue, "symbol": symbol},
            f"{symbol}@perpetual": {**perp, "venue": venue, "symbol": f"{symbol}@perpetual"},
        }
        perp_venues.append(venue)

    if not books:
        return {
            "ok": False,
            "source": "canonical_truth_bus",
            "symbol": symbol,
            "reason": "venue_perpetual_books_unavailable",
            "book_source": "unavailable",
            "live_anchored": False,
            "computed": False,
            "synthetic_forbidden": True,
            "perp_leg": "required_venue_futures",
        }

    try:
        funding_raw = get_live_funding(require_live=True, symbol=symbol)
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "source": "canonical_truth_bus",
            "symbol": symbol,
            "reason": f"live_funding_unavailable:{type(exc).__name__}",
            "book_source": "venue_l2_spot_perp",
            "live_anchored": True,
            "computed": False,
            "synthetic_forbidden": True,
            "perp_venues": perp_venues,
        }

    funding_rates: dict[str, dict[str, dict[str, Any]]] = {}
    for venue, syms in funding_raw.items():
        row = syms.get(symbol)
        if not row or row.get("synthetic"):
            continue
        funding_rates[venue] = {
            symbol: {
                "funding_rate": float(row["funding_rate"]),
                "timestamp": row.get("timestamp") or datetime.now(UTC).isoformat(),
                "next_funding_time": row.get("next_funding_time"),
                "source": row.get("source"),
            }
        }
    if not funding_rates:
        return {
            "ok": False,
            "source": "canonical_truth_bus",
            "symbol": symbol,
            "reason": "venue_funding_unavailable",
            "book_source": "venue_l2_spot_perp",
            "live_anchored": True,
            "computed": False,
            "synthetic_forbidden": True,
        }

    live_source = "canonical_truth_bus_venue_l2_spot_perp_funding"
    spot_futures: Any = []
    funding: Any = []
    try:
        spot_futures = calculate_spot_futures_premium(books) or []
    except Exception as exc:  # noqa: BLE001
        spot_futures = {"error": type(exc).__name__}
    try:
        funding = (
            calculate_funding_arbitrage(
                funding_rates,
                order_books=books,
                allow_indicative_without_depth=False,
            )
            or []
        )
    except Exception as exc:  # noqa: BLE001
        funding = {"error": type(exc).__name__}
    return {
        "ok": True,
        "source": "arbitrage_engine",
        "symbol": symbol,
        "spot_futures_count": len(spot_futures) if isinstance(spot_futures, list) else 0,
        "funding_count": len(funding) if isinstance(funding, list) else 0,
        "spot_futures": spot_futures if isinstance(spot_futures, list) else spot_futures,
        "funding": funding if isinstance(funding, list) else funding,
        "computed": True,
        "book_source": live_source,
        "live_anchored": True,
        "perp_leg": "venue_futures",
        "funding_source": "venue_funding",
        "perp_venues": perp_venues,
        "synthetic_hardcoded_books": False,
        "fabricated_depth": False,
    }


def build_super_terminal(*, symbol: str = "BTC/USDT", org_id: str = "default") -> dict[str, Any]:
    """Assemble Super Terminal pack from live product modules (not marketing stubs)."""
    from canonical_adoption import adopt_symbol

    symbol = adopt_symbol(symbol)
    modules: dict[str, Any] = {}
    errors: list[str] = []

    try:
        import arbitrage_catalog

        cat = arbitrage_catalog.get_catalog() if hasattr(arbitrage_catalog, "get_catalog") else {}
        modules["arbitrage"] = {"ok": True, "source": "arbitrage_catalog", "catalog": cat}
    except Exception as exc:  # noqa: BLE001
        errors.append(f"arbitrage:{type(exc).__name__}")
        modules["arbitrage"] = {"ok": False}

    try:
        from whale_execution_evidence import whale_status

        modules["whales"] = {**whale_status(), "ok": True}
    except Exception as exc:  # noqa: BLE001
        errors.append(f"whales:{type(exc).__name__}")
        modules["whales"] = {"ok": False}

    try:
        import onchain_tracker as oc

        modules["onchain"] = {
            "ok": True,
            "module": oc.__name__,
            "api": "build_onchain_context_safe",
            "callable": callable(getattr(oc, "build_onchain_context_safe", None)),
        }
    except Exception as exc:  # noqa: BLE001
        errors.append(f"onchain:{type(exc).__name__}")
        modules["onchain"] = {"ok": False}

    try:
        from portfolio_intelligence import analyze_portfolio, portfolio_status

        modules["portfolio"] = {**portfolio_status(), "ok": True, "sample": analyze_portfolio([])}
    except Exception as exc:  # noqa: BLE001
        errors.append(f"portfolio:{type(exc).__name__}")
        modules["portfolio"] = {"ok": False}

    try:
        import research_lab as rl

        research_payload: dict[str, Any] = {"ok": True, "module": rl.__name__}
        if hasattr(rl, "research_status"):
            research_payload.update(rl.research_status())
        modules["research"] = research_payload
    except Exception as exc:  # noqa: BLE001
        errors.append(f"research:{type(exc).__name__}")
        modules["research"] = {"ok": False, "reason": str(exc)}

    try:
        from canonical_truth_bus import get_live_books
        from microstructure_intelligence import microstructure_status, order_book_microstructure

        live_books = get_live_books(require_live=True, symbol=symbol)
        sample_book = None
        sample_venue = None
        for venue, symbols in live_books.items():
            if symbol in symbols:
                sample_book = symbols[symbol]
                sample_venue = venue
                break
        if not sample_book:
            raise ValueError("microstructure_live_book_missing")
        modules["charts_microstructure"] = {
            **microstructure_status(),
            "ok": True,
            "book_source": f"canonical_truth_bus:{sample_venue}",
            "live_anchored": True,
            "sample": order_book_microstructure(sample_book, notional=10_000.0),
        }
    except Exception as exc:  # noqa: BLE001
        errors.append(f"microstructure:{type(exc).__name__}")
        modules["charts_microstructure"] = {
            "ok": False,
            "reason": str(exc),
            "live_anchored": False,
            "synthetic_forbidden": True,
        }

    try:
        from risk_intelligence import risk_intelligence_status

        modules["risk"] = {**risk_intelligence_status(), "ok": True}
    except Exception as exc:  # noqa: BLE001
        errors.append(f"risk:{type(exc).__name__}")
        modules["risk"] = {"ok": False}

    try:
        from decision_intelligence_engine import engine_status

        modules["decision"] = {**engine_status(), "ok": True}
    except Exception as exc:  # noqa: BLE001
        errors.append(f"decision:{type(exc).__name__}")
        modules["decision"] = {"ok": False}

    try:
        modules["derivatives"] = _derivatives_pack(symbol)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"derivatives:{type(exc).__name__}")
        modules["derivatives"] = {"ok": False}

    # Unified decision object — one coherent decision, not 7 dashboards.
    decision_object: dict[str, Any] = {}
    try:
        from decision_e2e import run_decision_e2e

        e2e = run_decision_e2e(symbol=symbol, org_id=org_id, notional=25_000.0)
        decision_object = e2e.get("decision_object") or {}
        modules["unified_decision"] = {
            "ok": bool(e2e.get("ok")),
            "executable": e2e.get("executable"),
            "graph_id": decision_object.get("graph_id"),
            "pipeline": decision_object.get("pipeline"),
        }
    except Exception as exc:  # noqa: BLE001
        errors.append(f"unified_decision:{type(exc).__name__}")
        modules["unified_decision"] = {"ok": False}

    ready = sum(1 for v in modules.values() if v.get("ok") is True)
    required = (
        "arbitrage",
        "whales",
        "onchain",
        "portfolio",
        "research",
        "charts_microstructure",
        "derivatives",
        "unified_decision",
    )
    required_ok = all(modules.get(k, {}).get("ok") for k in required)
    pack: dict[str, Any] = {
        "surface": "super_terminal",
        "symbol": symbol,
        "org_id": org_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "modules": modules,
        "decision_object": decision_object,
        "module_keys": sorted(modules.keys()),
        "errors": errors,
        "canonical_required": True,
        "canonical_adopted": True,
        "security": "institutional_principal",
        "verified_complete": False,
        "implementation_class": "PARTIAL",
        "product_complete": False,
        "modules_ready": ready,
        "required_ok": required_ok,
        "note": "Super Terminal = intelligence domains feeding one coherent decision_object.",
    }
    # Optional tenant brand apply (served surface) — never invents brand.
    try:
        from white_label import apply_brand_to_surface, get_brand

        if get_brand(org_id):
            branded = apply_brand_to_surface(org_id, pack)
            pack["branding"] = branded.get("surface", {}).get("branding")
            pack["brand_applied"] = bool(branded.get("brand_applied"))
            pack["api_title"] = branded.get("api_title")
            pack["product_name"] = branded.get("product_name")
        else:
            pack["brand_applied"] = False
    except Exception as exc:  # noqa: BLE001
        pack["brand_applied"] = False
        errors.append(f"white_label:{type(exc).__name__}")
        pack["errors"] = errors
    return pack


def super_terminal_status() -> dict[str, Any]:
    return {
        "surface": "super_terminal",
        "modules": ["charts", "arbitrage", "whales", "onchain", "derivatives", "portfolio", "research"],
        "verified_complete": False,
        "implementation_class": "PARTIAL",
        "product_complete": False,
        "endpoint": "/api/institutional/super-terminal",
    }
