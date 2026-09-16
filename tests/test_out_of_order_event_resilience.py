"""Out-of-order event resilience — single-gap remediation (Phase 4 integrity)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

APPLICABLE_PATHS = (
    "data_governance/streaming.py::evaluate_stream_gaps",
    "data_governance/streaming.py::evaluate_event_time_order",
    "data_governance/streaming.py::apply_ordered_stream_event",
    "data_governance/timestamps.py::build_timestamps",
    "data_governance/order_book.py::evaluate_order_book_integrity",
    "transport_webhook_env/webhook_lifecycle.py::check_replay_window",
    "billing/event_ordering.py::should_apply_provider_subscription_event",
    "billing/subscription_engine.py::sync_from_stripe_subscription",
)


@pytest.fixture
async def billing_user():
    import database
    from database import create_user, init_db

    await init_db()
    email = f"ooo-billing-{datetime.now(UTC).timestamp()}@blackdark.test"
    uid = await create_user(email, "pbkdf2_sha256$260000$deadbeef$" + "a" * 64, "OOO Billing")
    return {"id": uid, "email": email}


def test_stream_older_after_newer_keeps_newer_state():
    from data_governance.streaming import apply_ordered_stream_event

    state: dict = {}
    first = apply_ordered_stream_event(
        state,
        sequence_id=10,
        event_time=1000.0,
        payload={"price": 100.0, "verdict": "BUY"},
    )
    assert first["accepted"] is True
    assert first["mutated"] is True
    state = first["state"]

    stale = apply_ordered_stream_event(
        state,
        sequence_id=8,
        event_time=900.0,
        payload={"price": 50.0, "verdict": "SELL"},
    )
    assert stale["out_of_order"] is True
    assert stale["accepted"] is False
    assert stale["mutated"] is False
    assert stale["state"]["canonical_payload"]["price"] == 100.0
    assert stale["state"]["canonical_payload"]["verdict"] == "BUY"
    assert stale["state"]["last_sequence_id"] == 10


def test_stream_duplicate_same_version_is_idempotent():
    from data_governance.streaming import apply_ordered_stream_event

    state: dict = {}
    first = apply_ordered_stream_event(
        state,
        sequence_id=5,
        payload={"price": 42.0},
    )
    state = first["state"]
    dup = apply_ordered_stream_event(
        state,
        sequence_id=5,
        payload={"price": 1.0},
    )
    assert dup["duplicate"] is True
    assert dup["accepted"] is False
    assert dup["state"]["canonical_payload"]["price"] == 42.0


def test_event_time_regression_rejects_older_after_newer():
    from data_governance.streaming import apply_ordered_stream_event

    state: dict = {}
    newer = apply_ordered_stream_event(state, event_time=2000.0, payload={"freshness": "LIVE"})
    state = newer["state"]
    older = apply_ordered_stream_event(state, event_time=1500.0, payload={"freshness": "STALE"})
    assert older["out_of_order"] is True
    assert older["state"]["canonical_payload"]["freshness"] == "LIVE"


def test_replay_isolated_does_not_mutate_live_state():
    from data_governance.streaming import apply_ordered_stream_event

    state = {"last_sequence_id": 20, "canonical_payload": {"price": 99.0}}
    replay = apply_ordered_stream_event(
        state,
        sequence_id=21,
        payload={"price": 101.0},
        replay=True,
    )
    assert replay["replay"] is True
    assert replay["mutated"] is False
    assert replay["state"]["canonical_payload"]["price"] == 99.0
    assert replay["replay_state"]["canonical_payload"]["price"] == 101.0


def test_downstream_data_governance_not_regressed_by_stale_event_time():
    from data_governance.pipeline import evaluate_data_governance
    from data_governance.streaming import apply_ordered_stream_event

    stream_state: dict = {}
    accepted = apply_ordered_stream_event(
        stream_state,
        event_time=3000.0,
        payload={"symbol": "BTC", "quote_age_ms": 500, "price": 65000.0},
    )
    stream_state = accepted["state"]
    rejected = apply_ordered_stream_event(
        stream_state,
        event_time=2500.0,
        payload={"symbol": "BTC", "quote_age_ms": 999999, "price": 1.0},
    )
    assert rejected["out_of_order"] is True
    live_payload = rejected["state"]["canonical_payload"]
    result = evaluate_data_governance(live_payload, symbol="BTC")
    assert result["data_governance_state"] in {"ADMITTED", "DEGRADED"}
    assert result["data_governance"]["freshness"]["freshness_state"] in {
        "LIVE",
        "NEAR_LIVE",
        "DELAYED",
        "CACHED",
        "PARTIAL",
    }


def test_evaluate_stream_gaps_flags_out_of_order_sequence():
    from data_governance.streaming import evaluate_stream_gaps

    verdict = evaluate_stream_gaps(sequence_id=3, last_sequence_id=7)
    assert verdict["out_of_order"] is True
    assert verdict["accepted"] is False
    assert verdict["duplicate"] is False


def test_order_book_sequence_gap_does_not_claim_integrity():
    from data_governance.order_book import evaluate_order_book_integrity

    result = evaluate_order_book_integrity(
        {"bid": 100.0, "ask": 101.0, "freshness_ms": 100, "sequence_gap": True}
    )
    assert result["integrity_ok"] is False
    assert result["resync_required"] is True


@pytest.mark.asyncio
async def test_billing_older_subscription_event_does_not_rewind_plan(billing_user):
    from billing.subscription_engine import activate_checkout, sync_from_stripe_subscription
    from billing.subscription_store import get_by_user_id

    uid = int(billing_user["id"])
    email = billing_user["email"]
    now = datetime.now(UTC)
    newer_end = int((now + timedelta(days=30)).timestamp())
    older_end = int((now + timedelta(days=10)).timestamp())
    sub_id = f"sub_ooo_{int(now.timestamp())}"

    await activate_checkout(
        email=email,
        plan="elite",
        provider="stripe",
        provider_subscription_id=sub_id,
        provider_event_id=f"evt_newer_{sub_id}",
        user_id=uid,
    )

    newer_obj = {
        "id": sub_id,
        "status": "active",
        "metadata": {"tier": "elite"},
        "current_period_start": int(now.timestamp()),
        "current_period_end": newer_end,
        "cancel_at_period_end": False,
    }
    await sync_from_stripe_subscription(
        newer_obj,
        provider="stripe",
        provider_event_id=f"evt_sync_newer_{sub_id}",
        provider_event_created=int(now.timestamp()) + 100,
    )

    older_obj = {
        "id": sub_id,
        "status": "active",
        "metadata": {"tier": "pro"},
        "current_period_start": int((now - timedelta(days=20)).timestamp()),
        "current_period_end": older_end,
        "cancel_at_period_end": False,
    }
    stale = await sync_from_stripe_subscription(
        older_obj,
        provider="stripe",
        provider_event_id=f"evt_sync_older_{sub_id}",
        provider_event_created=int(now.timestamp()),
    )
    assert stale.get("out_of_order_ignored") is True

    current = await get_by_user_id(uid)
    assert current is not None
    assert current["plan"] == "elite"


def test_applicable_paths_inventory():
    assert len(APPLICABLE_PATHS) == 8
