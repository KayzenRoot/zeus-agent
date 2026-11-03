"""Behaviour contracts for owner review of staged skill writes."""

from __future__ import annotations

import json
import sys

import pytest

from hermes_cli import skills_review


def _record(**overrides):
    record = {
        "id": "abc12345",
        "action": "create",
        "summary": "create 'weekly-report' — Weekly report helper (2 KB)",
        "origin": "background_review",
        "created_at": 1000,
        "payload": {"action": "create", "name": "weekly-report", "content": "# Weekly Report Skill\n"},
    }
    record.update(overrides)
    return record


def test_lists_pending_summaries_without_payloads(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(skills_review.wa, "list_pending", lambda subsystem: [_record()])

    records = skills_review.pending_records()

    assert records == [
        {
            "id": "abc12345",
            "action": "create",
            "summary": "create 'weekly-report' — Weekly report helper (2 KB)",
            "origin": "background_review",
            "created_at": 1000,
        }
    ]


def test_diff_renders_the_exact_staged_content(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        skills_review.wa,
        "get_pending",
        lambda subsystem, proposal_id: _record() if proposal_id == "abc12345" else None,
    )

    assert "Weekly Report Skill" in skills_review.pending_diff("abc12345")
    assert skills_review.pending_diff("missing") is None


def test_approve_refuses_without_an_interactive_owner(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(skills_review.wa, "get_pending", lambda *args: _record())
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    calls: list = []
    monkeypatch.setattr(
        skills_review, "handle_pending_subcommand", lambda *args: calls.append(args) or "Approved 1"
    )

    code, output = skills_review.approve_pending("abc12345")

    assert code == 2
    assert "interactive terminal" in output
    assert calls == []


def test_approve_requires_the_exact_word(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(skills_review.wa, "get_pending", lambda *args: _record())
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _prompt: "yes")
    calls: list = []
    monkeypatch.setattr(
        skills_review, "handle_pending_subcommand", lambda *args: calls.append(args) or "Approved 1"
    )

    code, output = skills_review.approve_pending("abc12345")

    assert code == 1
    assert "Not approved" in output
    assert calls == []


def test_approve_applies_only_after_owner_approval(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(skills_review.wa, "get_pending", lambda *args: _record())
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _prompt: "APPROVE")
    calls: list = []
    monkeypatch.setattr(
        skills_review,
        "handle_pending_subcommand",
        lambda subsystem, args: calls.append((subsystem, args)) or "Approved 1 skill write(s).",
    )

    code, output = skills_review.approve_pending("abc12345")

    assert code == 0
    assert output.startswith("Approved 1")
    assert calls == [("skills", ["approve", "abc12345"])]


def test_reject_discards_without_applying(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(skills_review.wa, "get_pending", lambda *args: _record())
    calls: list = []
    monkeypatch.setattr(
        skills_review,
        "handle_pending_subcommand",
        lambda subsystem, args: calls.append((subsystem, args))
        or "Rejected pending skill write 'abc12345'.",
    )

    code, output = skills_review.reject_pending("abc12345")

    assert code == 0
    assert "Rejected" in output
    assert calls == [("skills", ["reject", "abc12345"])]


def test_cmd_review_list_json_and_unknown_action(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(skills_review.wa, "list_pending", lambda subsystem: [_record()])

    class Args:
        review_action = "list"
        json = True

    assert skills_review.cmd_review(Args()) == 0
    assert json.loads(capsys.readouterr().out)[0]["id"] == "abc12345"

    class Unknown:
        review_action = "explode"

    assert skills_review.cmd_review(Unknown()) == 1
    assert "Unknown review action" in capsys.readouterr().out


def test_skills_command_routes_review_and_keeps_the_exit_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from argparse import Namespace

    from hermes_cli import skills_hub

    monkeypatch.setattr("hermes_cli.skills_review.cmd_review", lambda args: 1)

    assert skills_hub.skills_command(Namespace(skills_action="review")) == 1
