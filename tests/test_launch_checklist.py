"""Tests for launch checklist."""

from __future__ import annotations


def test_launch_checklist_structure():
    from launch_checklist import launch_checklist

    data = launch_checklist()
    assert data["total_tasks"] >= 15
    assert len(data["days"]) == 5
    assert "launch_percent" in data
    assert "next_actions" in data


def test_launch_save():
    from launch_checklist import save_checklist

    data = save_checklist()
    assert "saved_to" in data
