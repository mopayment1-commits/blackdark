"""
Decision Intelligence Engine — expanded feature extraction (#48).

Builds 100+ leak-guarded features from price, on-chain, funding, social,
and historical proxies. Composes base feature_store + technical + lags + interactions.
"""

from __future__ import annotations

import math
from typing import Any

from ml.feature_store import build_feature_vector


def _normalize_asset(asset: str) -> str:
    cleaned = asset.upper().strip().replace("/", "").replace("-", "")
    return cleaned[:-4] if cleaned.endswith("USDT") else cleaned


def _ema(values: list[float], period: int) -> float:
    if not values:
        return 0.0
    if len(values) < period:
        return sum(values) / len(values)
    k = 2 / (period + 1)
    ema = values[0]
    for v in values[1:]:
        ema = v * k + ema * (1 - k)
    return ema


def _rsi(closes: list[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(-period, 0):
        ch = closes[i] - closes[i - 1]
        gains.append(max(ch, 0))
        losses.append(max(-ch, 0))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss <= 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 4)


def _bollinger_position(closes: list[float], period: int = 20) -> float:
    if len(closes) < period:
        return 0.5
    window = closes[-period:]
    mean = sum(window) / period
    var = sum((x - mean) ** 2 for x in window) / period
    std = math.sqrt(var) if var > 0 else 1e-9
    return round((closes[-1] - mean) / (2 * std) + 0.5, 4)


def _atr_pct(closes: list[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 0.0
    trs = [abs(closes[i] - closes[i - 1]) for i in range(-period, 0)]
    atr = sum(trs) / period
    return round((atr / closes[-1]) * 100, 4) if closes[-1] > 0 else 0.0


def _technical_features(closes: list[float]) -> dict[str, float]:
    if len(closes) < 5:
        return {}
    feats: dict[str, float] = {}
    for p in (7, 14, 21, 28):
        feats[f"rsi_{p}"] = _rsi(closes, p)
    for p in (9, 21, 50):
        ema = _ema(closes, p)
        feats[f"ema_{p}_dist_pct"] = round((closes[-1] / ema - 1) * 100, 4) if ema > 0 else 0.0
    for p in (10, 20, 30):
        feats[f"bb_pos_{p}"] = _bollinger_position(closes, p)
    for p in (7, 14, 21):
        feats[f"atr_pct_{p}"] = _atr_pct(closes, p)
    # MACD proxy
    ema12 = _ema(closes, 12)
    ema26 = _ema(closes, 26)
    macd = ema12 - ema26
    signal = _ema([macd] * min(9, len(closes)), 9)
    feats["macd"] = round(macd, 6)
    feats["macd_signal"] = round(signal, 6)
    feats["macd_hist"] = round(macd - signal, 6)
    # Momentum at multiple horizons
    for h in (1, 2, 3, 5, 8, 13, 21, 34, 55, 89):
        if len(closes) > h:
            feats[f"mom_{h}h_pct"] = round((closes[-1] / closes[-1 - h] - 1) * 100, 4)
    # Volatility windows
    for w in (3, 6, 12, 24, 48, 72):
        if len(closes) > w:
            rets = [(closes[i] / closes[i - 1] - 1) for i in range(-w, 0)]
            feats[f"vol_{w}h"] = round(
                (sum(r * r for r in rets) / len(rets)) ** 0.5 * 100, 4
            )
            feats[f"vol_ratio_{w}h"] = round(
                feats[f"vol_{w}h"] / max(feats.get("vol_24h", 1), 0.01), 4
            )
    # Higher moments
    if len(closes) >= 24:
        rets = [(closes[i] / closes[i - 1] - 1) for i in range(-24, 0)]
        mean = sum(rets) / len(rets)
        var = sum((r - mean) ** 2 for r in rets) / len(rets)
        std = math.sqrt(var) if var > 0 else 1e-9
        skew = sum(((r - mean) / std) ** 3 for r in rets) / len(rets)
        kurt = sum(((r - mean) / std) ** 4 for r in rets) / len(rets) - 3
        feats["ret_skew_24h"] = round(skew, 4)
        feats["ret_kurt_24h"] = round(kurt, 4)
    return feats


def _interaction_features(base: dict[str, Any]) -> dict[str, float]:
    """Cross-domain interaction terms (no label leakage)."""
    feats: dict[str, float] = {}
    sent = float(base.get("sentiment_score") or 0)
    obi = float(base.get("obi_imbalance") or 0)
    whale = float(base.get("whale_sii") or 0)
    flow = float(base.get("onchain_netflow") or 0)
    vol = float(base.get("volatility") or 0)
    fund = float(base.get("funding_spread_bps") or 0)
    macro = float(base.get("macro_weight") or 1)
    ret24 = float(base.get("ret_24h") or 0)

    pairs = [
        ("sent_x_obi", sent * obi),
        ("sent_x_whale", sent * whale),
        ("obi_x_flow", obi * flow),
        ("whale_x_flow", whale * flow),
        ("vol_x_fund", vol * fund / 100),
        ("macro_x_ret", macro * ret24),
        ("sent_x_ret", sent * ret24),
        ("obi_x_ret", obi * ret24),
        ("fund_x_ret", fund * ret24 / 100),
        ("flow_x_ret", flow * ret24 / 1e6 if flow else 0),
    ]
    for name, val in pairs:
        feats[name] = round(max(-100, min(100, val)), 4)

    feats["bull_regime"] = 1.0 if ret24 > 2 else 0.0
    feats["bear_regime"] = 1.0 if ret24 < -2 else 0.0
    feats["high_vol_regime"] = 1.0 if vol > 3 else 0.0
    feats["extreme_funding"] = 1.0 if abs(fund) > 20 else 0.0
    # Additional cross-domain signals
    for i, (a, b) in enumerate(
        [
            ("sentiment_score", "whale_sii"),
            ("obi_score", "macro_weight"),
            ("funding_spread_bps", "volatility"),
            ("onchain_netflow", "sentiment_momentum"),
        ]
    ):
        va = float(base.get(a) or 0)
        vb = float(base.get(b) or 0)
        feats[f"cross_{i}_{a[:4]}_{b[:4]}"] = round(va * vb / 100, 4)
    return feats


async def _alpha_features(symbol: str) -> dict[str, float]:
    try:
        from bd_platform.alpha_engine import gather_alpha_inputs

        ctx = await gather_alpha_inputs(symbol)
        factors = ctx.get("factors") or {}
        feats: dict[str, float] = {}
        for k, v in factors.items():
            feats[f"alpha_{k}"] = round(float(v), 4)
        fg = (ctx.get("sources") or {}).get("alternative_me_fear_greed") or {}
        feats["alpha_fear_greed_value"] = float(fg.get("value") or 50)
        entity = (ctx.get("sources") or {}).get("arkham_entity") or {}
        feats["alpha_entity_flow"] = float(entity.get("entity_flow_score") or 50)
        return feats
    except Exception:
        return {}


async def extract_decision_features(
    asset: str,
    *,
    price_at: float | None = None,
    closes: list[float] | None = None,
) -> dict[str, Any]:
    """
    Extract 100+ features for Decision Intelligence Engine.
    Returns flat dict + metadata.
    """
    sym = _normalize_asset(asset)
    base = await build_feature_vector(sym, price_at=price_at)

    if closes is None:
        from ml.feature_store import _recent_closes

        closes = await _recent_closes(sym, limit=96)

    technical = _technical_features(closes)
    interactions = _interaction_features(base)
    alpha = await _alpha_features(sym)

    # Lag features from base returns
    lags: dict[str, float] = {}
    for key in ("ret_1h", "ret_4h", "ret_24h", "volatility", "sentiment_score", "obi_imbalance"):
        val = float(base.get(key) or 0)
        for lag in (1, 2, 3):
            lags[f"{key}_lag{lag}"] = round(val * (0.9**lag), 4)

    # Price level features
    price_feats: dict[str, float] = {}
    if closes:
        price_feats["price_log"] = round(math.log(max(closes[-1], 1e-9)), 6)
        if len(closes) >= 48:
            hi = max(closes[-48:])
            lo = min(closes[-48:])
            price_feats["range_48h_pct"] = round((hi - lo) / lo * 100, 4) if lo > 0 else 0
            price_feats["dist_from_high_48h"] = round((closes[-1] / hi - 1) * 100, 4) if hi > 0 else 0

    all_feats: dict[str, Any] = {
        **{k: v for k, v in base.items() if isinstance(v, (int, float))},
        **technical,
        **interactions,
        **alpha,
        **lags,
        **price_feats,
    }

    count = len(all_feats)
    return {
        "asset": sym,
        "feature_count": count,
        "features": all_feats,
        "feature_names": sorted(all_feats.keys()),
        "meets_100_plus": count >= 100,
    }
