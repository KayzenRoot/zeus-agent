"""Behaviour contracts for owner-approved self-healing."""

from __future__ import annotations

import json
import sqlite3
import sys
import time
from pathlib import Path

import pytest

import zeus_entitlement
from hermes_cli import heal_cmd, heal_store


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(heal_cmd, "get_hermes_home", lambda: tmp_path)
    monkeypatch.setattr(
        zeus_entitlement,
        "status",
        lambda: zeus_entitlement.EntitlementStatus(
            True, "active", plan="annual", expires_at=None
        ),
    )
    return tmp_path


def test_diagnose_proposes_gateway_restart_without_changing_anything(
    home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(heal_cmd, "_gateway_snapshot", lambda: (None, False))

    plan = heal_cmd.diagnose()

    assert plan["gateway_running"] is False
    assert [finding["code"] for finding in plan["findings"]] == ["gateway-not-running"]
    assert plan["actions"] == [
        {
            "action": "restart-gateway",
            "reason": "The local gateway is not running.",
            "requires_owner_approval": True,
        }
    ]
    assert not (home / "logs" / "heal-audit.jsonl").exists()


def test_status_prints_findings_without_crashing(
    home: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(heal_cmd, "_gateway_snapshot", lambda: (None, False))

    class Args:
        json = False

    assert heal_cmd.cmd_status(Args()) == 0
    output = capsys.readouterr().out
    assert "gateway-not-running" in output
    assert "Entitlement: active" in output


def test_apply_refuses_without_an_interactive_owner(
    home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(heal_cmd, "_gateway_snapshot", lambda: (None, False))
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)

    assert heal_cmd.apply_action("restart-gateway") == 2
    assert not (home / "logs" / "heal-audit.jsonl").exists()


def test_apply_requires_the_exact_approval_word(
    home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(heal_cmd, "_gateway_snapshot", lambda: (None, False))
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _prompt: "yes")

    assert heal_cmd.apply_action("restart-gateway") == 1
    assert not (home / "logs" / "heal-audit.jsonl").exists()


def test_apply_runs_only_the_approved_action_and_audits_it(
    home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(heal_cmd, "_gateway_snapshot", lambda: (None, False))
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _prompt: "APPROVE")
    calls: list[str] = []

    def fake_restart() -> int:
        calls.append("restart-gateway")
        return 0

    monkeypatch.setattr(heal_cmd, "_restart_gateway", fake_restart)

    assert heal_cmd.apply_action("restart-gateway") == 0
    assert calls == ["restart-gateway"]
    audit = home / "logs" / "heal-audit.jsonl"
    entry = json.loads(audit.read_text(encoding="utf-8").strip())
    assert entry["action"] == "restart-gateway"
    assert entry["result"] == "ok"
    if sys.platform != "win32":
        assert audit.stat().st_mode & 0o777 == 0o600


def test_apply_refuses_an_action_outside_the_plan(
    home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(heal_cmd, "_gateway_snapshot", lambda: ({"pid": 1}, True))

    assert heal_cmd.apply_action("restart-gateway") == 1


def _state_db(home: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(home / "state.db")
    connection.executescript(
        """
        CREATE TABLE sessions (
            id TEXT PRIMARY KEY, started_at REAL, last_activity_at REAL
        );
        CREATE TABLE messages (
            session_id TEXT, role TEXT, content TEXT, tool_name TEXT, timestamp REAL
        );
        CREATE TABLE session_admissions (target_session_id TEXT, status TEXT);
        CREATE TABLE worker_executions (
            execution_id TEXT, session_id TEXT, status TEXT
        );
        """
    )
    return connection


def test_diagnose_reports_a_stuck_turn_without_proposing_a_destructive_fix(
    home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    old = int(time.time()) - 3600
    connection = _state_db(home)
    connection.execute(
        "INSERT INTO sessions (id, started_at, last_activity_at) VALUES ('s1', ?, ?)",
        (old, old),
    )
    connection.execute(
        "INSERT INTO messages (session_id, role, content, timestamp) VALUES ('s1', 'user', 'hi', ?)",
        (old,),
    )
    connection.execute(
        "INSERT INTO session_admissions (target_session_id, status) VALUES ('s1', 'started')"
    )
    connection.commit()
    connection.close()
    monkeypatch.setattr(heal_cmd, "_gateway_snapshot", lambda: ({"pid": 1}, True))

    plan = heal_cmd.diagnose()

    finding = next(item for item in plan["findings"] if item["code"] == "stuck-turn")
    assert finding["action"] is None
    assert "s1" in finding["summary"]


def test_diagnose_reports_repeated_tool_failures(
    home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    now = int(time.time())
    connection = _state_db(home)
    for index in range(3):
        connection.execute(
            "INSERT INTO messages (session_id, role, content, tool_name, timestamp) "
            "VALUES ('s1', 'tool', 'Error: boom', 'terminal', ?)",
            (now - index,),
        )
    connection.commit()
    connection.close()
    monkeypatch.setattr(heal_cmd, "_gateway_snapshot", lambda: ({"pid": 1}, True))

    plan = heal_cmd.diagnose()

    finding = next(
        item for item in plan["findings"] if item["code"] == "tool-failures-repeated"
    )
    assert "terminal" in finding["summary"]
    assert finding["action"] is None


def test_propose_skips_a_live_duplicate_and_persists_findings(
    home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(heal_cmd, "_gateway_snapshot", lambda: (None, False))
    plan = heal_cmd.diagnose()

    first = heal_cmd.propose_actions(plan)
    second = heal_cmd.propose_actions(plan)

    assert len(first) == 1
    assert second == []
    proposal = heal_store.load_proposal(home, first[0]["id"])
    assert proposal is not None
    assert proposal["action"] == "restart-gateway"
    assert proposal["findings"][0]["code"] == "gateway-not-running"
    assert proposal["rollback"]


def test_approve_requires_an_interactive_owner(
    home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(heal_cmd, "_gateway_snapshot", lambda: (None, False))
    proposal = heal_cmd.propose_actions()[0]
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)

    class Args:
        proposal_id = proposal["id"]

    assert heal_cmd.cmd_approve(Args()) == 2
    assert heal_store.load_proposal(home, proposal["id"])["status"] == "pending"


def test_approve_requires_the_owner_word_and_executes_only_the_proposal(
    home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(heal_cmd, "_gateway_snapshot", lambda: (None, False))
    proposal = heal_cmd.propose_actions()[0]
    calls: list[str] = []
    monkeypatch.setattr(heal_cmd, "_execute_action", lambda action: calls.append(action) or 0)
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _prompt: "yes")

    class Args:
        proposal_id = proposal["id"]

    assert heal_cmd.cmd_approve(Args()) == 1
    assert calls == []
    assert heal_store.load_proposal(home, proposal["id"])["status"] == "pending"

    monkeypatch.setattr("builtins.input", lambda _prompt: "APPROVE")
    assert heal_cmd.cmd_approve(Args()) == 0
    assert calls == ["restart-gateway"]
    assert heal_store.load_proposal(home, proposal["id"])["status"] == "executed"
