"""Tests for safe analytical oracle language (no Buy Now / Do Not Touch)."""

from __future__ import annotations

from oracle_safe_language import (
    SAFE_VERDICT_BULLISH,
    SAFE_VERDICT_RISK,
    accepted_analytical_sentence,
    build_analytical_prompt,
    contains_banned_advice_language,
    format_analytical_sentence,
    normalize_llm_sentence,
)


def test_prompt_never_requests_buy_now():
    prompt = build_analytical_prompt(asset="BTC", score=72, summary="Momentum up")
    lower = prompt.lower()
    assert "buy now" not in lower
    assert "do not touch" not in lower
    assert "probability" in lower


def test_rules_sentence_is_analytical():
    sentence = format_analytical_sentence(
        "ETH",
        probability=68,
        reason="Net edge after fees remains positive",
        verdict=SAFE_VERDICT_BULLISH,
    )
    assert "Buy Now" not in sentence
    assert "Do Not Touch" not in sentence
    assert accepted_analytical_sentence(sentence)


def test_banned_llm_output_is_normalized():
    verdict, sentence = normalize_llm_sentence(
        "Buy Now — BTC: strong momentum",
        asset="BTC",
        score=80,
    )
    assert verdict in {SAFE_VERDICT_BULLISH, SAFE_VERDICT_RISK, "NEUTRAL_OBSERVE"}
    assert not contains_banned_advice_language(sentence)
    assert "informational analytics only" in sentence.lower()


def test_risk_sentence_uses_elevated_language():
    sentence = format_analytical_sentence(
        "SOL",
        probability=35,
        reason="Slippage exceeds edge",
        verdict=SAFE_VERDICT_RISK,
    )
    assert "elevated risk" in sentence.lower()
    assert accepted_analytical_sentence(sentence)
