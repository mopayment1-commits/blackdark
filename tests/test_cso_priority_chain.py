"""CSO priority chain binding — features-first rejected; gate enforced."""

from __future__ import annotations

import asyncio
from pathlib import Path

from httpx import ASGITransport, AsyncClient


def test_chain_shape_and_rule():
    from cso_priority_chain import build_cso_priority_chain, evaluate_feature_proposal

    chain = build_cso_priority_chain()
    assert chain["status"] == "binding"
    assert chain["all_done_for_agreed_scope"] is True
    assert chain["deferred_code_count"] == 0
    assert chain["stage_count"] == 8
    assert chain["stages"][0]["id"] == "product_excellence"
    assert chain["stages"][-1]["id"] == "acquisition_leverage"
    assert "features" in chain["rejected_old_chain"]
    assert "habit" in chain["binding_rule"].lower() or "عادة" in chain["binding_rule"]
    assert chain["strict_confirmation"]["old_features_first_rejected"] is True
    assert chain["strict_confirmation"]["percent_complete_agreed_scope"] == 100

    deny = evaluate_feature_proposal(
        title="20 indicators for valuation slides",
        levers=["acquisition_leverage", "strategic_moat"],
    )
    assert deny["allowed"] is False

    allow = evaluate_feature_proposal(
        title="Daily Trust Pulse habit reminder",
        raises_habit=True,
        raises_revenue=True,
    )
    assert allow["allowed"] is True


def test_closure_smoke():
    from cso_priority_chain import build_cso_priority_closure

    # Closure builder is sync (dict-returning); do not wrap with asyncio.run.
    closure = build_cso_priority_closure()
    assert closure["code_complete_zero_deferred"] is True
    assert closure["gate_smoke"]["vanity_rejected"] is True
    assert closure["gate_smoke"]["habit_loop_allowed"] is True
    assert closure["world_class_100_complete"] is False


def test_wiring_files():
    heroes = Path("api/routers/heroes.py").read_text(encoding="utf-8")
    trust = Path("trust_os.py").read_text(encoding="utf-8")
    canon = Path("docs/CANONICAL_BINDING.md").read_text(encoding="utf-8")
    assert "/api/strategy/priority-chain" in heroes
    assert "/api/public/cso-priority-closure" in heroes
    assert "cso_priority_chain" in trust
    assert "CSO_PRIORITY_CHAIN_BINDING_AR.md" in canon
    assert Path("docs/CSO_PRIORITY_CHAIN_BINDING_AR.md").exists()
    assert Path("templates/priority_chain.html").exists()
    assert Path("cso_priority_chain.py").exists()
    assert "priority-chain" in Path("dashboard.py").read_text(encoding="utf-8")
    assert "CSO Priority Chain" in Path("templates/utility.html").read_text(encoding="utf-8")


def test_public_paths():
    from public_api_docs import path_is_public

    assert path_is_public("/api/strategy/priority-chain") is True
    assert path_is_public("/api/public/cso-priority-closure") is True
    assert path_is_public("/priority-chain") is True


def test_http_surfaces():
    async def _run():
        from dashboard import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/api/strategy/priority-chain")
            assert r.status_code == 200
            assert r.json()["all_done_for_agreed_scope"] is True

            e = await client.get(
                "/api/strategy/priority-chain/evaluate",
                params=[("title", "vanity"), ("lever", "acquisition_leverage")],
            )
            assert e.status_code == 200
            assert e.json()["allowed"] is False

            c = await client.get("/api/public/cso-priority-closure")
            assert c.status_code == 200
            assert c.json()["deferred_code_count"] == 0

            p = await client.get("/priority-chain")
            assert p.status_code == 200
            assert "Priority Chain" in p.text

            t = await client.get("/api/trust-os")
            assert t.status_code == 200
            assert "cso_priority_chain" in t.json()

    asyncio.run(_run())
