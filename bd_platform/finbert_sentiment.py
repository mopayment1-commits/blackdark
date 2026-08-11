"""FinBERT financial sentiment — optional transformers with VADER fallback."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("BLACKDARK.FinBERT")

_FINBERT_PIPELINE: Any = None


def _load_finbert() -> Any | None:
    global _FINBERT_PIPELINE
    if _FINBERT_PIPELINE is not None:
        return _FINBERT_PIPELINE
    try:
        from transformers import pipeline

        _FINBERT_PIPELINE = pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert",
            truncation=True,
            max_length=512,
        )
        logger.info("FinBERT loaded (ProsusAI/finbert).")
        return _FINBERT_PIPELINE
    except Exception as exc:
        logger.debug("FinBERT unavailable: %s", exc)
        return None


def _vader_score(text: str) -> dict[str, Any]:
    from sentiment_engine import analyze_sentiment_score_detailed

    result = analyze_sentiment_score_detailed(text)
    return {
        "compound": result.sentiment_score,
        "analyzer": result.analyzer,
    }


def analyze_text(text: str) -> dict[str, Any]:
    """Score financial text; FinBERT when installed else VADER."""
    text = (text or "").strip()
    if not text:
        return {"engine": "none", "label": "neutral", "score": 0.0, "confidence": 0.0}

    pipe = _load_finbert()
    if pipe is not None:
        try:
            result = pipe(text[:2000])[0]
            label = str(result.get("label") or "neutral").lower()
            conf = float(result.get("score") or 0.5)
            if label in {"positive", "bullish"}:
                signed = conf
            elif label in {"negative", "bearish"}:
                signed = -conf
            else:
                signed = 0.0
            return {
                "engine": "finbert",
                "label": label,
                "score": round(signed, 4),
                "confidence": round(conf, 4),
                "raw": result,
            }
        except Exception as exc:
            logger.warning("FinBERT inference failed: %s", exc)

    vader = _vader_score(text)
    compound = float(vader.get("compound") or 0)
    if compound > 0.05:
        label = "positive"
    elif compound < -0.05:
        label = "negative"
    else:
        label = "neutral"
    return {
        "engine": "vader_fallback",
        "label": label,
        "score": round(compound, 4),
        "confidence": round(abs(compound), 4),
        "raw": vader,
    }


async def analyze_headlines(headlines: list[str], *, limit: int = 20) -> dict[str, Any]:
    items = []
    for headline in headlines[:limit]:
        analysis = analyze_text(headline)
        items.append({"text": headline[:200], **analysis})
    if not items:
        return {"count": 0, "aggregate_score": 0.0, "engine": "none", "items": []}
    avg = sum(i["score"] for i in items) / len(items)
    engines = {i["engine"] for i in items}
    return {
        "count": len(items),
        "aggregate_score": round(avg, 4),
        "engine": "finbert" if "finbert" in engines else "vader_fallback",
        "items": items,
    }
