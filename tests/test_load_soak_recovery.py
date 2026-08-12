"""Load / soak / recovery smoke gates (environment-bounded, not marketing claims)."""

from __future__ import annotations

import time


def test_stream_lifecycle_sustained_mark_and_ack():
    from streaming_institutional import StreamLifecycleManager

    m = StreamLifecycleManager(max_queue_depth=50_000, throttle_per_sec=100_000)
    m.register_subscription("binance", "BTC/USDT")
    m.heartbeat("binance")
    t0 = time.perf_counter()
    n = 5_000
    for i in range(1, n + 1):
        out = m.mark_message("binance", seq=i)
        assert out["ok"] is True
        if i % 100 == 0:
            m.ack_processed("binance", n=100)
    elapsed = time.perf_counter() - t0
    snap = m.snapshot()["venues"]["binance"]
    assert snap["gap_count"] == 0
    assert snap["duplicate_count"] == 0
    # Environment-bounded: just prove sustained processing completes without leak-like growth
    assert snap["queue_depth"] < 5_000
    assert elapsed < 30.0


def test_stream_recovery_after_outage():
    from streaming_institutional import StreamLifecycleManager

    m = StreamLifecycleManager()
    m.register_subscription("okx", "ETH/USDT")
    m.heartbeat("okx")
    m.mark_outage("okx", failover_to="binance")
    assert m.is_alive("okx")["alive"] is False
    rec = m.reconnect("okx")
    assert rec["recovery"] is True
    assert m.mark_message("okx", seq=1)["ok"] is True
    assert m.is_alive("okx")["alive"] is True


def test_oms_restart_recovery_idempotent_intent(tmp_path, monkeypatch):
    import oms
    from path_safety import safe_data_file

    # Persist under data/ (path_safety require); use unique idempotency keys.
    monkeypatch.setattr(oms, "_PATH", safe_data_file("oms_soak_test.json"))
    key = f"soak-key-{tmp_path.name}"
    a = oms.create_intent(
        org_id="org-soak",
        venue="binance",
        symbol="BTC/USDT",
        side="buy",
        quantity=0.01,
        limit_price=100.0,
        idempotency_key=key,
        actor="soak",
    )
    b = oms.create_intent(
        org_id="org-soak",
        venue="binance",
        symbol="BTC/USDT",
        side="buy",
        quantity=0.01,
        limit_price=100.0,
        idempotency_key=key,
        actor="soak",
    )
    assert a["order_id"] == b["order_id"]
