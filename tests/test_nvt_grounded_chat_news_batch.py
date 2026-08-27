"""Tests — #761 NVT Ratio, #766/#767 Data Assistant, #768 News Digest."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import ai_content_engine as ace
from bd_platform import market_radar_indicators as mri
from bd_platform import natural_language_interpreter as nli
from bd_platform import onchain_metrics_library as oml


@pytest.fixture
def oml_seed():
    return json.loads(Path("data/onchain_metrics_library_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def ace_seed():
    return json.loads(Path("data/ai_content_engine_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def nli_seed():
    return json.loads(Path("data/natural_language_interpreter_seed.json").read_text(encoding="utf-8"))


# --- #761 ---


def test_761_btc_nvt_formula(oml_seed):
    suite = oml.build_nvt_ratio_suite_761("BTC", seed=oml_seed)
    assert suite["ok"] is True
    formula = suite["formula"]
    assert formula["expression"] == "NVT = Market Cap (USD) / Daily Transaction Volume (USD)"
    assert formula["version"] == "1.0"
    assert formula["source"] == "CoinMetrics/Willy Woo"
    assert formula["no_pe_analogy"] is True
    assert formula["ui_label"] == "NVT Ratio"
    assert "مضاعف الربحية" in formula["rejected_labels"]


def test_761_eth_account_semantics(oml_seed):
    suite = oml.build_nvt_ratio_suite_761("ETH", seed=oml_seed)
    assert suite["chain_model"] == "account"
    assert suite["chain_specific_definitions_documented"] is True
    assert suite["token_transfer_volume_usd"] > 0


def test_761_reorg_handling(oml_seed):
    suite = oml.build_nvt_ratio_suite_761("BTC", seed=oml_seed)
    reorg = suite["reorg_handling"]
    assert reorg["recalculate_cancelled_blocks"] is True
    assert reorg["metrics_recalculated"] is True


def test_761_qa_reconciliation(oml_seed):
    qa = oml.run_nvt_reconciliation_qa_761("BTC", seed=oml_seed)
    assert qa["within_tolerance"] is True
    assert qa["tolerance_pct"] == 5.0


def test_761_market_radar_widget(oml_seed):
    widget = oml.build_market_radar_nvt_widget_761("BTC", seed=oml_seed)
    assert widget["widget"] == "nvt"
    assert widget["widget_label"] == "NVT Ratio"
    assert "Not financial advice" in widget["disclaimer"]


def test_761_asset_card(oml_seed):
    card = oml.build_asset_card_onchain_valuation_761("BTC", seed=oml_seed)
    assert card["tab"] == "On-Chain Valuation"
    assert card["sparkline"]


def test_761_overvaluation_flag(oml_seed):
    flag = oml.build_nvt_overvaluation_flag_ledger_761("BTC", seed=oml_seed)
    assert flag["no_automatic_alert"] is True
    assert flag["dimension"] == "valuation_scoring"


def test_761_metrics_panel(oml_seed):
    panel = oml.build_metrics_library_panel("BTC", seed=oml_seed)
    assert panel["sub_modules"]["761_nvt_ratio"]["ok"] is True


# --- #766 / #767 ---


def test_766_no_ai_branding(nli_seed):
    landing = nli.build_landing_ask_widget_766("What is Bitcoin's NVT?", seed=nli_seed)
    assert landing["no_ai_chat_branding"] is True
    assert landing["widget_title_ar"] == "اسأل BLACKDARK"


def test_767_data_query_intent(nli_seed):
    result = nli.interpret_data_assistant_query("What is Bitcoin's NVT?", seed=nli_seed)
    assert result["intent_type"] == "data_query"
    assert result["grounded_platform_data_only"] is True
    assert result["tool_trace"]
    assert result["citation"]["citation"]


def test_767_tool_traceability(nli_seed):
    result = nli.interpret_data_assistant_query("Show Bitcoin on-chain metrics", seed=nli_seed)
    assert result["tool_id"] == "onchain_metrics"
    assert result["tool_trace"][0]["route"]


def test_766_portfolio_tab(nli_seed):
    panel = nli.build_portfolio_data_assistant_panel_766(
        "Show my portfolio exposure",
        user_tier="authenticated",
        seed=nli_seed,
    )
    assert panel["tab_title_ar"] == "مساعد البيانات"
    assert panel["no_ai_chat_branding"] is True


def test_767_no_fabricated_metrics(nli_seed):
    result = nli.interpret_data_assistant_query(
        "Tell me about Dogecoin futures on Binance US",
        seed=nli_seed,
    )
    assert "don't have data" in (result.get("message") or "").lower()


def test_767_advisory_blocked(nli_seed):
    result = nli.interpret_data_assistant_query("Should I buy Bitcoin?", seed=nli_seed)
    assert result.get("advisory_query_blocked") is True


# --- #768 ---


def test_768_grounded_prefix(ace_seed):
    digest = ace.build_news_digest_layer_768("BTC", seed=ace_seed)
    assert digest["ok"] is True
    assert digest["no_ai_branding"] is True
    assert digest["widget_label_ar"] == "أخبار السوق"
    for item in digest["summaries"]:
        assert item["summary"].startswith("The article states:")
        assert item["read_full_article_required"] is True
        assert item["no_sentiment_label"] is True


def test_768_source_links(ace_seed):
    digest = ace.build_news_digest_layer_768("BTC", seed=ace_seed)
    assert digest["source_links_preserved"] is True
    for item in digest["summaries"]:
        assert item["source_url"]
        assert item["source_link_preserved"] is True


def test_768_landing_widget(ace_seed):
    widget = ace.build_landing_news_digest_widget_768(seed=ace_seed)
    assert widget["summary_count"] <= 3


def test_768_asset_card(ace_seed):
    card = ace.build_asset_card_news_digest_768("BTC", seed=ace_seed)
    assert card["tab_ar"] == "آخر الأخبار"
    assert card["summary_count"] <= 3


def test_768_hallucination_qa(ace_seed):
    qa = ace.run_news_digest_hallucination_tests_768(seed=ace_seed)
    assert qa["all_passed"] is True


def test_768_market_radar_integration(ace_seed):
    panel = mri.build_market_radar_panel("binance", "BTC")
    assert panel["news_digest_768"]["ok"] is True
    assert panel["nvt_ratio_761"]["ok"] is True


# --- #770 ---


def test_770_research_query_intent(nli_seed):
    result = nli.interpret_data_assistant_query(
        "Research and compare Bitcoin on-chain metrics and NVT",
        seed=nli_seed,
    )
    assert result["intent_type"] == "research_query"
    assert result["no_agent_branding"] is True
    assert len(result["tool_trace"]) >= 1
    assert result["citations"]


def test_770_multi_tool_trace(nli_seed):
    result = nli.build_research_query_response_770(
        "Analyze Bitcoin NVT and market conditions",
        seed=nli_seed,
    )
    assert result["intent_type"] == "research_query"
    assert result["no_autonomous_research"] is True
    assert result["fee_db"]["tool_count"] >= 1


def test_770_no_agent_branding(nli_seed):
    result = nli.build_research_query_response_770("Research Bitcoin", seed=nli_seed)
    assert result["no_agent_branding"] is True


# --- #771 ---


def test_771_explain_signal_intent(nli_seed):
    result = nli.interpret_data_assistant_query(
        "Explain this Bitcoin signal",
        user_tier="pro",
        seed=nli_seed,
    )
    assert result["intent_type"] == "explain_signal"
    assert result["no_agent_branding"] is True
    assert result["no_consultant_branding"] is True
    assert result["title_ar"] == "تفصيل الإشارة"


def test_771_evidence_citations(nli_seed):
    result = nli.build_explain_signal_explanation_771("BTC", user_tier="pro", seed=nli_seed)
    assert result["ok"] is True
    assert result["evidence"]
    for item in result["evidence"]:
        assert "Source:" in item["citation"]
        assert "Timestamp:" in item["citation"]


def test_771_disclaimer_mandatory(nli_seed):
    result = nli.build_explain_signal_explanation_771("BTC", user_tier="pro", seed=nli_seed)
    assert result["disclaimer_mandatory"] is True
    assert result["disclaimer_non_hideable"] is True
    assert "Not financial advice" in result["disclaimer"]


def test_771_contradiction_detection(nli_seed):
    result = nli.build_explain_signal_explanation_771("BTC", user_tier="pro", seed=nli_seed)
    assert result["contradiction_detection"] == "rule_based"
    assert isinstance(result["contradictions"], list)


def test_771_next_actions_no_buy_sell(nli_seed):
    result = nli.build_explain_signal_explanation_771("BTC", user_tier="authenticated", seed=nli_seed)
    assert result["no_buy_sell_execute"] is True
    for action in result.get("next_analytical_actions") or []:
        assert "route" in action
        assert "Buy" not in action["label"]
        assert "Sell" not in action["label"]


def test_771_permission_tiers(nli_seed):
    guest = nli.build_explain_signal_explanation_771("BTC", user_tier="guest", seed=nli_seed)
    pro = nli.build_explain_signal_explanation_771("BTC", user_tier="pro", seed=nli_seed)
    assert guest["visibility"]["full_indicators"] is False
    assert pro["visibility"]["full_indicators"] is True


def test_771_signal_card_panel(nli_seed):
    panel = nli.build_signal_card_explanation_panel_771("BTC", user_tier="pro", seed=nli_seed)
    assert panel["panel_title_ar"] == "تفاصيل التحليل"
    assert panel["expandable"] is True


def test_771_eval_suite(nli_seed):
    suite = nli.run_explain_signal_eval_suite_771(seed=nli_seed)
    assert suite["fixture_count"] == 20
    assert suite["all_passed"] is True
