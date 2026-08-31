"""Tests — #601 #612 #615 #617 #618 merged features batch."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import onchain_metrics_library as oml
from bd_platform import portfolio_intelligence_engine as pie
from bd_platform import stablecoin_health_monitor as shm
from bd_platform import transaction_flow_view as tfv


@pytest.fixture
def stablecoin_seed(tmp_path, monkeypatch):
    p = tmp_path / "stablecoin_health_monitor_seed.json"
    p.write_text(Path("data/stablecoin_health_monitor_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(shm, "_SEED_PATH", p)
    return p


@pytest.fixture
def metrics_seed(tmp_path, monkeypatch):
    p = tmp_path / "onchain_metrics_library_seed.json"
    p.write_text(Path("data/onchain_metrics_library_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(oml, "_SEED_PATH", p)
    monkeypatch.setattr(shm, "_SEED_PATH", tmp_path / "stablecoin_health_monitor_seed.json")
    stablecoin = Path("data/stablecoin_health_monitor_seed.json").read_text(encoding="utf-8")
    (tmp_path / "stablecoin_health_monitor_seed.json").write_text(stablecoin, encoding="utf-8")
    return p


@pytest.fixture
def flow_seed(tmp_path, monkeypatch):
    p = tmp_path / "transaction_flow_view_seed.json"
    p.write_text(Path("data/transaction_flow_view_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(tfv, "_SEED_PATH", p)
    return p


@pytest.fixture
def portfolio_seed(tmp_path, monkeypatch):
    p = tmp_path / "portfolio_intelligence_engine_seed.json"
    p.write_text(Path("data/portfolio_intelligence_engine_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(pie, "_SEED_PATH", p)
    return p


# --- #601 Stablecoin Exchange Reserve ---


def test_601_reserve_entity_labels(stablecoin_seed):
    reserve = shm.build_stablecoin_exchange_reserve()
    assert reserve["ok"] is True
    assert reserve["entity_labels_required"] is True
    assert len(reserve["by_exchange"]) >= 2
    assert all("wallets" in ex for ex in reserve["by_exchange"])


def test_601_missing_not_zero(stablecoin_seed):
    reserve = shm.build_stablecoin_exchange_reserve()
    assert reserve["missing_stale_explicit"] is True
    assert reserve["missing_count"] >= 1
    okx = next(e for e in reserve["by_exchange"] if e["exchange_id"] == "okx")
    assert okx["wallets"][0]["missing_display"] is not None


def test_601_buying_power_context(stablecoin_seed):
    reserve = shm.build_stablecoin_exchange_reserve()
    bp = reserve["buying_power_context"]
    assert bp["total_reserve_usd"] > 0
    assert bp["interpretation"] == "accumulated_buying_power_on_exchanges"


def test_601_depeg_suspend(stablecoin_seed, monkeypatch):
    seed = json.loads(stablecoin_seed.read_text(encoding="utf-8"))
    seed["stablecoins"]["USDT"]["price_usd"] = 0.99
    stablecoin_seed.write_text(json.dumps(seed), encoding="utf-8")
    reserve = shm.build_stablecoin_exchange_reserve()
    assert reserve["calculation_suspended"] is True
    assert reserve["total_reserve_usd"] != 0


def test_601_market_radar_widget(stablecoin_seed):
    widget = shm.build_market_radar_stablecoin_reserve_trend()
    assert widget["surface"] == "market_radar"
    assert widget["widget"] == "stablecoin_reserve_trend"


def test_601_reconciliation(stablecoin_seed):
    result = shm.run_reconciliation_tests()
    ids = {c["id"] for c in result["checks"]}
    assert "601_entity_labels" in ids
    assert "601_depeg_handling" in ids


# --- #612 Transaction Volume Intelligence ---


def test_612_volume_policy(metrics_seed):
    vol = oml.build_transaction_volume_intelligence("BTC")
    assert vol["ok"] is True
    excluded = vol["excluded_counts"]
    assert excluded["internal_exchange"] >= 1
    assert excluded["self_transfer"] >= 1
    assert excluded["dust"] >= 1
    assert excluded["spam"] >= 1


def test_612_price_at_tx_time(metrics_seed):
    vol = oml.build_transaction_volume_intelligence("BTC")
    align = vol["price_timestamp_alignment"]
    assert align["method"] == "usd_value_at_tx_time"
    assert align["not_current_price"] is True


def test_612_volume_chart(metrics_seed):
    vol = oml.build_transaction_volume_intelligence("ETH")
    assert len(vol["volume_chart"]) >= 3
    assert vol["anomaly"]["detected"] is True


def test_612_historical_qa_parity(metrics_seed):
    qa = oml.run_tx_volume_historical_qa()
    assert qa["all_passed"] is True
    assert qa["test_count"] >= 3


def test_612_merged_in_library_panel(metrics_seed):
    panel = oml.build_metrics_library_panel("BTC", prefer_live=False)
    assert "612_transaction_volume_intelligence" in panel["sub_modules"]
    assert "601_stablecoin_exchange_reserve" in panel["sub_modules"]


# --- #615 Transaction Flow View ---


def test_615_hop_limit(flow_seed):
    graph = tfv.build_transaction_flow_graph("0xbinance_hot")
    assert graph["hop_limit_enforced"] is True
    assert graph["max_hops"] == 3


def test_615_entity_aggregation(flow_seed):
    graph = tfv.build_transaction_flow_graph("0xbinance_hot")
    nodes = graph["graph"].get("nodes") or []
    binance_nodes = [n for n in nodes if n.get("entity_id") == "binance"]
    if nodes:
        assert any(n.get("aggregated") for n in binance_nodes)


def test_615_deterministic_path(flow_seed):
    g1 = tfv.build_transaction_flow_graph("0xbinance_hot")
    g2 = tfv.build_transaction_flow_graph("0xbinance_hot")
    assert g1["deterministic_path_id"] == g2["deterministic_path_id"]


def test_615_provenance(flow_seed):
    graph = tfv.build_transaction_flow_graph("0xbinance_hot")
    assert graph["provenance_per_edge"] is True


def test_615_summary_mode_large_graph(flow_seed):
    graph = tfv.build_transaction_flow_graph("0xlarge_hub")
    assert graph["graph"]["mode"] == "summary"
    assert graph["graph"]["node_count"] > 100


def test_615_trace_path(flow_seed):
    trace = tfv.trace_path("0xbinance_hot", "coinbase")
    assert trace.get("ok") is True or trace.get("error") == "no_path_within_hop_limit"


def test_615_reconciliation(flow_seed):
    result = tfv.run_reconciliation_tests()
    assert result["ok"] is True


# --- #617 Entry/Exit Timeline ---


def test_617_fifo_timeline(portfolio_seed):
    timeline = pie.build_entry_exit_timeline("demo_wallet")
    assert timeline["ok"] is True
    assert timeline["fifo_only"] is True
    assert len(timeline["timeline"]) >= 4


def test_617_transfers_not_sales(portfolio_seed):
    timeline = pie.build_entry_exit_timeline("demo_wallet")
    transfers = [e for e in timeline["timeline"] if e.get("action") == "transfer"]
    assert len(transfers) >= 1
    assert transfers[0]["pnl_impact"] == "none"


def test_617_partial_exits(portfolio_seed):
    timeline = pie.build_entry_exit_timeline("demo_wallet")
    assert timeline["partial_exits_supported"] is True
    assert timeline["partial_exit_count"] >= 1


def test_617_breakeven_sync(portfolio_seed):
    timeline = pie.build_entry_exit_timeline("demo_wallet")
    sync = timeline.get("breakeven_sync_404") or {}
    assert sync.get("auto_updated") is True


# --- #618 Historical Performance ---


def test_618_sufficient_sample(portfolio_seed):
    perf = pie.build_wallet_historical_performance_card("demo_wallet")
    assert perf["confidence"] == "sufficient"
    metrics = perf["metrics"]
    assert metrics["win_rate_pct"] is not None
    assert metrics["max_drawdown_pct"] is not None
    assert metrics["sharpe_ratio"] is not None
    assert metrics["consistency_score"] is not None


def test_618_insufficient_sample(portfolio_seed):
    perf = pie.build_wallet_historical_performance_card("small_wallet")
    assert perf["confidence"] == "insufficient_data"
    assert "بيانات غير كافية" in perf["display"]


def test_618_exclude_open_positions(portfolio_seed):
    perf = pie.build_wallet_historical_performance_card("demo_wallet")
    assert perf["open_positions_excluded"] >= 1
    assert perf["exclude_incomplete_trades"] is True


def test_618_integrated_panel(portfolio_seed):
    panel = pie.build_integrated_panel()
    assert panel.get("entry_exit_timeline_617", {}).get("ok") is True
    assert panel.get("historical_performance_618", {}).get("ok") is True


def test_618_reconciliation(portfolio_seed):
    result = pie.run_reconciliation_tests()
    ids = {c["id"] for c in result["checks"]}
    assert "entry_exit_617" in ids
    assert "performance_618" in ids
    assert "fifo_only" in ids
