"""Behaviour contracts for owner-approved self-healing."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

import zeus_entitlement
from hermes_cli import heal_cmd


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
