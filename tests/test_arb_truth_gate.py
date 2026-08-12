"""Live arb scan must attach D3 Net-Edge Truth and skip rejects from alerts."""

from __future__ import annotations

import inspect


def test_scan_source_wires_net_edge_truth():
    import arbitrage_service

    scan_src = inspect.getsource(arbitrage_service.scan_arbitrage_opportunities)
    truth_src = inspect.getsource(arbitrage_service._apply_truth_to_row)
    gates_src = inspect.getsource(arbitrage_service._apply_constitution_scan_gates)
    assert "_apply_constitution_scan_gates" in scan_src
    assert "_apply_truth_to_row" in gates_src
    assert "compute_net_edge_truth" in truth_src
    assert "truth_rejected" in truth_src
    assert "net_edge_truth_reject" in truth_src


def test_alert_processor_skips_truth_rejects():
    import arbitrage_service

    src = inspect.getsource(arbitrage_service.process_arbitrage_alerts)
    assert "is_alertable" in src
    assert "constitution_gates" in src


def test_enrichment_does_not_overwrite_prediction_id():
    from decision_enrichment import enrich_oracle_decision

    out = enrich_oracle_decision(
        {
            "symbol": "BTC",
            "opportunity_score": 70,
            "verdict": "Buy Now",
            "prediction_id": 4242,
            "price": 90000,
        },
        ux_mode="pro",
        lang="en",
        register_signal=True,
    )
    assert out.get("prediction_id") == 4242
    assert (out.get("signal_registry") or {}).get("signal_id")
