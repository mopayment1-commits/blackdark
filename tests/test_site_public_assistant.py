from site_public_assistant import reply_site_assistant


def test_explains_visible_pulse():
    out = reply_site_assistant(
        "What is shown?",
        {"trust_pulse": {"action": "WAIT", "symbol": "BTC", "sentence": "Wait for clarity."}},
    )
    assert "WAIT" in out["reply"]
    assert "BTC" in out["reply"]
    assert out["refusal"] is False
