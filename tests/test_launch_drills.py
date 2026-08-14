"""Cheap launch drills that must not import the full dashboard unless required."""

from __future__ import annotations


def test_counsel_and_pentest_missing_are_fail_not_untested():
    from launch_drills import drill_counsel_artifacts, drill_independent_pentest_artifact

    c = drill_counsel_artifacts()
    p = drill_independent_pentest_artifact()
    assert c["verdict"] in {"PASS", "FAIL"}
    assert p["verdict"] in {"PASS", "FAIL"}
    assert c["verdict"] != "NOT_TESTED"
    assert p["verdict"] != "NOT_TESTED"


def test_rate_limit_and_panic_and_sqlite():
    from launch_drills import drill_panic_freeze, drill_rate_limit_abuse, drill_sqlite_restore

    rl = drill_rate_limit_abuse()
    assert rl["verdict"] == "PASS", rl
    pz = drill_panic_freeze()
    assert pz["verdict"] == "PASS", pz
    sq = drill_sqlite_restore()
    assert sq["verdict"] in {"PASS", "FAIL"}, sq


def test_feature_flag_and_infra_files():
    from launch_drills import drill_feature_flag, drill_infra_files

    ff = drill_feature_flag()
    assert ff["verdict"] == "PASS", ff
    inf = drill_infra_files()
    assert inf["verdict"] in {"PASS", "FAIL"}, inf
    assert inf["verdict"] != "NOT_TESTED"


def test_compose_yaml_merge_and_stripe_sandbox_evaluated():
    from launch_drills import drill_compose_yaml_merge, drill_stripe_sandbox

    y = drill_compose_yaml_merge()
    assert y["verdict"] == "PASS", y
    s = drill_stripe_sandbox()
    assert s["verdict"] in {"PASS", "FAIL"}
    assert s["verdict"] != "NOT_TESTED"


def test_ha_architecture_and_executable_l2_and_compose_config():
    from launch_drills import drill_compose_config, drill_executable_l2_scope, drill_ha_architecture

    ha = drill_ha_architecture()
    assert ha["verdict"] == "PASS", ha
    l2 = drill_executable_l2_scope()
    assert l2["verdict"] == "PASS", l2
    cc = drill_compose_config()
    assert cc["verdict"] in {"PASS", "FAIL"}, cc
    assert cc["verdict"] != "NOT_TESTED"


def test_ai_fallback_does_not_crash():
    from launch_drills import drill_ai_fallback

    r = drill_ai_fallback()
    assert r["verdict"] in {"PASS", "FAIL"}, r
    assert r["id"] == "ai_fallback"
