"""Behavioral coverage for governance.rfc9457."""

from __future__ import annotations

from governance.rfc9457 import is_problem_detail, problem_response


def test_problem_response_and_validator():
    body = problem_response(
        status=400,
        title="Bad Request",
        detail="invalid",
        instance="/x",
        correlation_id="cid-1",
        extensions={"code": "BD-TEST"},
    )
    assert body["correlation_id"] == "cid-1"
    assert body["code"] == "BD-TEST"
    assert is_problem_detail(body) is True
    assert is_problem_detail({"title": "x"}) is False
