from __future__ import annotations

from site_public_assistant import REFUSAL, reply_site_assistant, resolve_query_symbol


def test_explains_visible_pulse():
    out = reply_site_assistant(
        "What is shown?",
        {"trust_pulse": {"action": "WAIT", "symbol": "BTC", "sentence": "Wait for clarity."}},
    )
    assert "WAIT" in out["reply"]
    assert "BTC" in out["reply"]
    assert out["refusal"] is False
    assert REFUSAL in out["reply"]


def test_eth_price_differs_from_btc_pulse():
    out = reply_site_assistant(
        "سعر ETH",
        {"trust_pulse": {"action": "WAIT", "symbol": "BTC", "sentence": "WAIT on BTC score 60/100."}},
        oracle_ctx={"symbol": "ETH", "price": 3200.5, "opportunity_score": 72, "decision_action": "WAIT"},
    )
    assert "ETH" in out["reply"]
    assert "3200" in out["reply"] or "3,200" in out["reply"]
    assert "BTC" in out["reply"]
    assert "WAIT on BTC score 60/100" not in out["reply"]


def test_arabic_followup_why_links_thread():
    thread = [
        {"role": "user", "topic": "سعر ETH", "symbol": "ETH", "intent": "price"},
        {
            "role": "bot",
            "topic": "ETH price line",
            "summary": "You asked about ETH price. Public quick read for ETH",
            "symbol": "ETH",
            "intent": "price",
        },
    ]
    out = reply_site_assistant(
        "وما سبب الانتظار؟",
        {"trust_pulse": {"action": "WAIT", "symbol": "BTC", "sentence": "WAIT on BTC score 60/100."}},
        thread=thread,
        oracle_ctx={
            "symbol": "ETH",
            "decision_action": "WAIT",
            "decision_sentence": "ETH conditions not met for act.",
            "opportunity_score": 72,
        },
    )
    assert "Continuing" in out["reply"] or "ETH" in out["reply"]
    assert "WAIT on BTC score 60/100" not in out["reply"]
    assert out["turn"]["intent"] == "why"
    assert out["turn"]["symbol"] == "ETH"


def test_resolve_symbol_from_arabic():
    assert resolve_query_symbol("سعر ETH", None) == "ETH"
    assert resolve_query_symbol("سعر إيثريوم", None) == "ETH"


def test_two_questions_do_not_share_identical_reply():
    ctx = {"trust_pulse": {"action": "WAIT", "symbol": "BTC", "sentence": "WAIT on BTC score 60/100."}}
    a = reply_site_assistant("سعر ETH", ctx, oracle_ctx={"symbol": "ETH", "price": 1, "opportunity_score": 50})
    b = reply_site_assistant("وما سبب الانتظار؟", ctx, thread=sanitize_thread_from(a))
    assert a["reply"] != b["reply"]


def sanitize_thread_from(first_out):
    return [
        {"role": "user", "topic": "سعر ETH", "symbol": "ETH", "intent": "price"},
        {"role": "bot", "topic": first_out["reply"][:80], "symbol": "ETH", "intent": "price"},
    ]
