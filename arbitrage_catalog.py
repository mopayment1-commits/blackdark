"""
BLACKDARK — 77-Type Arbitrage Catalog (Wave 6 / Excel roadmap).

Taxonomy of all arbitrage strategies from the product spec. Live types map to
the existing engine; proxy types score from multi-modal signals; planned types
are catalogued for B2B / acquisition decks.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.ArbitrageCatalog")

CatalogStatus = Literal["live", "proxy", "planned"]

# id, category, name_en, name_ar, status, engine_kind (optional)
_CATALOG_RAW: list[tuple[int, str, str, str, CatalogStatus, str | None]] = [
    (1, "cross_exchange", "Buy low / sell high across CEX", "شراء رخيص وبيع غالي بين المنصات", "live", "cross_exchange"),
    (2, "cross_exchange", "CEX vs DEX price gap", "فجوة أسعار مركزية vs لامركزية", "planned", None),
    (3, "cross_exchange", "Three-venue profit cycle", "دورة ربح عبر 3 منصات", "proxy", "cross_exchange"),
    (4, "cross_exchange", "Stale quote / update lag snipe", "قنص أخطاء التسعير أثناء التحديث", "proxy", "cross_exchange"),
    (5, "cross_exchange", "Liquidity dump absorption", "شراء عند ضخ سيولة يدفع السعر لأسفل", "proxy", None),
    (6, "cross_exchange", "Fast vs slow feed latency", "استغلال سرعة تحديث البيانات بين المنصات", "proxy", "cross_exchange"),
    (7, "cross_exchange", "Geographic / local liquidity spread", "فروق القيود الجغرافية والسيولة المحلية", "planned", None),
    (8, "cross_exchange", "Withdrawal open/close window", "فارق فتح/إغلاق السحب بين المنصات", "planned", None),
    (9, "cross_exchange", "Multi-asset cross-venue scan", "مراقبة مئات الأصول عبر المنصات", "live", "cross_exchange"),
    (10, "cross_exchange", "Tier-1 vs tier-2 venue spread", "فارق منصات كبرى vs متوسطة", "live", "cross_exchange"),
    (11, "triangular", "Classic 3-leg loop (USDT→BTC→ETH→USDT)", "مراجحة ثلاثية داخل منصة واحدة", "live", "triangular"),
    (12, "triangular", "Stablecoin peg spread (USDT/USDC/DAI)", "فروق العملات المستقرة", "proxy", "triangular"),
    (13, "triangular", "Fiat-crypto hybrid loop", "دمج العملات المحلية مع الرقمية", "planned", None),
    (14, "triangular", "Circular 4+ asset loop", "حلقة دائرية لأكثر من 4 أصول", "live", "triangular"),
    (15, "triangular", "Cross-triangular combo path", "دمج مراجحة بينية + ثلاثية", "proxy", None),
    (16, "derivatives", "Long spot / short perp (positive basis)", "شراء فوري + بيع عقد عند Premium", "live", "spot_futures"),
    (17, "derivatives", "Short spot / long perp (negative basis)", "بيع فوري + شراء عقد عند Discount", "live", "spot_futures"),
    (18, "derivatives", "Funding rate harvest (long/short perp pair)", "جمع رسوم التمويل بمراكز متعاكسة", "live", "funding"),
    (19, "derivatives", "Calendar spread (Mar vs Jun futures)", "مراجحة عقود بتواريخ استحقاق مختلفة", "planned", None),
    (20, "derivatives", "Options vs spot mispricing", "انحراف خيارات vs السعر الفوري", "planned", None),
    (21, "derivatives", "Perpetual vs quarterly contract", "عقد دائم vs ربع سنوي", "planned", None),
    (22, "derivatives", "Index vs derivative basis", "فارق المؤشر العام vs المشتق", "planned", None),
    (23, "defi", "Flash loan atomic arb (Aave)", "اقتراض فوري وتنفيذ في بلوك واحد", "planned", None),
    (24, "defi", "Uniswap vs SushiSwap pricing", "فروق صيغ التسعير بين DEX", "planned", None),
    (25, "defi", "Cross-chain bridge spread", "مراجحة عبر الجسور بين الشبكات", "planned", None),
    (26, "defi", "MEV / slippage capture", "استغلال Slippage وترتيب المعاملات", "planned", None),
    (27, "defi", "Liquidation discounted collateral", "شراء أصول مرهونة بخصم أثناء التصفية", "planned", None),
    (28, "defi", "ETH vs stETH peg", "فارق ETH الأصلي vs stETH", "planned", None),
    (29, "defi", "BTC vs WBTC wrap spread", "فارق BTC vs WBTC", "planned", None),
    (30, "defi", "Stablecoin depeg recovery", "شراء stable عند <$1 وبيع عند الاستقرار", "proxy", None),
    (31, "defi", "Block-ordering / priority MEV", "ترتيب المعاملات داخل البلوك", "planned", None),
    (32, "defi", "Gas-optimized micro arb bot", "بوت مراجحة صغيرة بتقليل الغاز", "planned", None),
    (33, "liquidity", "DEX liquidity-add snipe", "شراء فور إضافة السيولة", "planned", None),
    (34, "liquidity", "Dual-exchange new listing", "إدراج عملة جديدة على منصتين", "proxy", None),
    (35, "liquidity", "Pre-market vs spot at launch", "ما قبل الإدراج vs السوق الفوري", "planned", None),
    (36, "liquidity", "Token rights pre-distribution", "شراء حقوق قبل التوزيع", "planned", None),
    (37, "liquidity", "Launchpad cross-platform", "مراجحة منصات الإطلاق", "planned", None),
    (38, "statistical", "Pair correlation deviation", "انحراف إحصائي بين عملتين مرتبطتين", "proxy", None),
    (39, "statistical", "Mean reversion from SMA", "ابتعاد السعر عن المتوسط المتوقع", "proxy", None),
    (40, "statistical", "Cointegration gap model", "تكامل مشترك لتحديد فجوات الأسعار", "proxy", None),
    (41, "statistical", "Correlation break (e.g. BTC/Gold)", "انكسار الارتباط المعتاد", "proxy", None),
    (42, "statistical", "AI predictive gap (seconds ahead)", "تنبؤ AI بفجوة قبل حدوثها", "proxy", None),
    (43, "etf", "Spot BTC vs ETF premium", "مراجحة ETF البيتكوين vs Spot", "planned", None),
    (44, "etf", "Real stock vs tokenized equity", "سهم حقيقي vs مرمز على البلوكشين", "planned", None),
    (45, "etf", "Basket token vs index constituents", "سلة عملات vs توكن المؤشر", "planned", None),
    (46, "event", "Hard fork free-coin capture", "شراء قبل الانقسام وبيع العملة الجديدة", "planned", None),
    (47, "event", "Network migration spread", "فارق تحول التوكن لشبكة جديدة", "planned", None),
    (48, "event", "Major listing announcement snipe", "قنص إعلان إدراج Binance", "proxy", None),
    (49, "event", "Regulatory jurisdiction spread", "فروق قرارات تنظيمية بين الدول", "planned", None),
    (50, "event", "Unbonding discount tokens", "شراء توكنات بخصم أثناء فك القفل", "planned", None),
    (51, "event", "Delisting short arb", "بيع مكشوف عند شطب من منصة", "planned", None),
    (52, "event", "Merger token spread", "مراجحة توكنات مشاريع اندمجت", "planned", None),
    (53, "microstructure", "Order book imbalance edge", "مراجحة اختلال دفتر الطلبات", "proxy", None),
    (54, "microstructure", "Depth-walking executable spread", "تنفيذ مع عمق السيولة الكامل", "live", "cross_exchange"),
    (55, "microstructure", "Open interest divergence", "انحراف Open Interest بين المنصات", "proxy", None),
    (56, "microstructure", "Funding convergence trade", "تقارب معدلات التمويل", "live", "funding"),
    (57, "microstructure", "Maker-taker fee optimization", "تحسين رسوم Maker/Taker", "proxy", None),
    (58, "microstructure", "HFT latency scalp", "مراجحة سرعة عالية التردد", "proxy", None),
    (59, "microstructure", "Whale flow front-run proxy", "استغلال تدفقات الحيتان", "proxy", None),
    (60, "statistical", "Pairs trading statistical deviation", "تداول أزواج — انحراف إحصائي", "proxy", None),
    (61, "statistical", "Mean reversion bot", "بوت العودة للمتوسط", "proxy", None),
    (62, "statistical", "Cointegration pairs model", "نموذج التكامل المشترك", "proxy", None),
    (63, "statistical", "Macro correlation break", "انكسار ارتباط ماكرو (ذهب/بيتكوين)", "proxy", None),
    (64, "statistical", "AI gap prediction engine", "ذكاء اصطناعي يتنبأ بالفجوة", "proxy", None),
    (65, "etf", "ETF vs spot BTC arb", "ETF vs بيتكوين فوري", "planned", None),
    (66, "etf", "Equity vs on-chain token", "أسهم vs توكنات على السلسلة", "planned", None),
    (67, "etf", "Index basket vs token", "مؤشر vs سلة توكنات", "planned", None),
    (68, "event", "Fork airdrop capture", "التقاط airdrop الانقسام", "planned", None),
    (69, "event", "Chain migration arb", "مراجحة هجرة الشبكة", "planned", None),
    (70, "event", "Listing pump cross-venue", "ضخ الإدراج عبر منصات", "proxy", None),
    (71, "event", "Regulatory arbitrage", "مراجحة تنظيمية", "planned", None),
    (72, "event", "Unbonding period discount", "خصم فترة Unbonding", "planned", None),
    (73, "event", "Delisting fade short", "بيع مكشوف عند الشطب", "planned", None),
    (74, "event", "M&A token merger spread", "فارق اندماج المشاريع", "planned", None),
    (75, "onchain_model", "NVT ratio signal arb", "إشارة NVT (قيمة/معاملات)", "proxy", None),
    (76, "onchain_model", "Realized cap divergence", "انحراف Realized Cap", "proxy", None),
    (77, "onchain_model", "NUPL sentiment extreme", "NUPL — خوف/طمع متطرف", "proxy", None),
]

ARBITRAGE_CATALOG: list[dict[str, Any]] = [
    {
        "id": row[0],
        "category": row[1],
        "name": row[2],
        "name_en": row[2],
        "status": row[4],
        "engine_kind": row[5],
    }
    for row in _CATALOG_RAW
]


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def get_catalog(*, category: str | None = None, status: str | None = None) -> dict[str, Any]:
    items = ARBITRAGE_CATALOG
    if category:
        items = [i for i in items if i["category"] == category]
    if status:
        items = [i for i in items if i["status"] == status]
    by_status = {
        "live": sum(1 for i in ARBITRAGE_CATALOG if i["status"] == "live"),
        "proxy": sum(1 for i in ARBITRAGE_CATALOG if i["status"] == "proxy"),
        "planned": sum(1 for i in ARBITRAGE_CATALOG if i["status"] == "planned"),
    }
    categories = sorted({i["category"] for i in ARBITRAGE_CATALOG})
    return {
        "total_types": len(ARBITRAGE_CATALOG),
        "counts_by_status": by_status,
        "categories": categories,
        "types": items,
        "timestamp": _utcnow_iso(),
    }


def _proxy_score_for_type(
    type_id: int,
    *,
    institutional: dict,
    macro: dict | None,
    sentiment: dict | None,
    oracle_accuracy: float,
) -> float | None:
    """Heuristic 0–100 score for proxy/planned types without live order-book match."""
    whale_count = len(institutional.get("whale_alerts") or [])
    sector_flows = len(institutional.get("sector_flows") or [])
    macro_regime = (macro or {}).get("macro_regime") or "Neutral"
    sent_raw = (sentiment or {}).get("sentiment_compound_index") or {}
    if isinstance(sent_raw, dict):
        sent_values = list(sent_raw.values())
    elif isinstance(sent_raw, list):
        sent_values = [float(x.get("compound", x)) if isinstance(x, dict) else float(x) for x in sent_raw]
    else:
        sent_values = []
    avg_sent = sum(float(v) for v in sent_values) / len(sent_values) if sent_values else 0.0

    scores: dict[int, float] = {
        4: min(85, 40 + whale_count * 8),
        5: min(90, 35 + whale_count * 10),
        6: min(80, 45 + sector_flows * 5),
        12: 55.0,
        30: 50.0,
        34: min(75, 30 + whale_count * 12),
        38: min(70, 40 + abs(avg_sent) * 20),
        39: min(65, 35 + oracle_accuracy * 0.3),
        40: min(60, 30 + oracle_accuracy * 0.25),
        41: 55.0 if macro_regime != "Neutral" else 40.0,
        42: min(85, oracle_accuracy * 0.85),
        48: min(80, 25 + whale_count * 15),
        53: min(75, 40 + sector_flows * 6),
        55: min(70, 35 + sector_flows * 5),
        57: 52.0,
        58: min(78, 50 + whale_count * 5),
        59: min(88, 30 + whale_count * 14),
        60: min(68, 38 + oracle_accuracy * 0.28),
        61: min(65, 35 + oracle_accuracy * 0.25),
        62: 58.0,
        63: 62.0 if macro_regime != "Neutral" else 45.0,
        64: min(90, oracle_accuracy * 0.9),
        70: min(82, 28 + whale_count * 13),
        75: min(72, 45 + abs(avg_sent) * 15),
        76: min(68, 42 + oracle_accuracy * 0.2),
        77: min(75, 50 + abs(avg_sent) * 18),
    }
    return scores.get(type_id)


def _opportunities_by_kind(live_scan: dict[str, Any]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for opp in live_scan.get("opportunities") or []:
        kind = opp.get("kind") or "unknown"
        grouped.setdefault(kind, []).append(opp)
    return grouped


def _live_catalog_row(row: dict[str, Any], matches: list[dict]) -> bool:
    if not matches:
        return False
    best = max(matches, key=lambda item: float(item.get("net_profit_usdt") or 0))
    row["active"] = True
    row["score"] = min(
        100.0,
        max(0.0, 50.0 + float(best.get("net_profit_percent") or 0) * 10),
    )
    row["matches"] = [best]
    return True


def _proxy_catalog_row(
    row: dict[str, Any],
    entry: dict[str, Any],
    *,
    institutional: dict[str, Any],
    macro: dict[str, Any],
    sentiment: dict[str, Any],
    oracle_accuracy: float,
) -> bool:
    score = _proxy_score_for_type(
        entry["id"],
        institutional=institutional,
        macro=macro,
        sentiment=sentiment,
        oracle_accuracy=oracle_accuracy,
    )
    if score is None or score < 40:
        return False
    row["active"] = True
    row["score"] = round(score, 1)
    return True


def _catalog_base_row(entry: dict[str, Any]) -> dict[str, Any]:
    row = dict(entry)
    row["active"] = False
    row["score"] = 0.0
    row["matches"] = []
    return row


async def scan_arbitrage_catalog(
    quote_amount: float | None = None,
    *,
    min_score: float = 0.0,
) -> dict[str, Any]:
    """Match live engine output + proxy scores to the 77-type catalog."""
    import config
    from arbitrage_service import scan_arbitrage_opportunities
    from database import fetch_latest_macro_market_log, fetch_oracle_audit_stats
    from sentiment_engine import build_sentiment_context_safe
    from whale_tracker import get_latest_institutional_context

    live_scan = await scan_arbitrage_opportunities(quote_amount=quote_amount, prefer_live=True)
    institutional = await get_latest_institutional_context()
    sentiment = await build_sentiment_context_safe(list(config.WHITELIST_ASSETS))
    macro = await fetch_latest_macro_market_log()
    audit = await fetch_oracle_audit_stats(limit=20)
    oracle_accuracy = float(audit.get("average_accuracy_percent") or 0)
    opps_by_kind = _opportunities_by_kind(live_scan)

    results: list[dict[str, Any]] = []
    active_live = 0
    active_proxy = 0

    for entry in ARBITRAGE_CATALOG:
        row = _catalog_base_row(entry)

        if (
            entry["status"] == "live"
            and entry.get("engine_kind")
            and _live_catalog_row(row, opps_by_kind.get(entry["engine_kind"]) or [])
        ):
            active_live += 1
        elif entry["status"] == "proxy":
            if _proxy_catalog_row(
                row,
                entry,
                institutional=institutional,
                macro=macro,
                sentiment=sentiment,
                oracle_accuracy=oracle_accuracy,
            ):
                active_proxy += 1

        if row["score"] >= min_score:
            results.append(row)

    results.sort(key=lambda x: (x["active"], x["score"]), reverse=True)

    return {
        "catalog_total": len(ARBITRAGE_CATALOG),
        "active_live_types": active_live,
        "active_proxy_types": active_proxy,
        "live_opportunities_found": live_scan.get("profitable_count", 0),
        "data_source": live_scan.get("data_source"),
        "top_live_opportunity": live_scan.get("top_opportunity"),
        "active_types": [r for r in results if r["active"]],
        "catalog_scan": results,
        "timestamp": _utcnow_iso(),
    }
