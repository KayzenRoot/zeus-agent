"""Behaviour contracts for expiring, owner-approved healing proposals."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from hermes_cli import heal_store


def _audit_events(home: Path) -> list[dict]:
    path = home / "logs" / "heal-audit.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_create_proposal_persists_rollback_findings_and_audit(tmp_path: Path) -> None:
    proposal = heal_store.create_proposal(
        tmp_path,
        action="restart-gateway",
        reason="gateway down",
        findings=[{"code": "gateway-not-running", "severity": "medium"}],
        now=1000,
    )

    path = tmp_path / "heal-proposals" / f"{proposal['id']}.json"
    stored = json.loads(path.read_text(encoding="utf-8"))
    assert stored["status"] == "pending"
    assert stored["created_at"] == 1000
    assert stored["expires_at"] == 1600
    assert "gateway restart" in stored["rollback"]
    assert stored["findings"][0]["code"] == "gateway-not-running"
    if sys.platform != "win32":
        assert path.stat().st_mode & 0o777 == 0o600
    assert _audit_events(tmp_path)[0]["event"] == "proposal.created"


def test_pending_actions_ignore_expired_proposals(tmp_path: Path) -> None:
    heal_store.create_proposal(
        tmp_path, action="restart-gateway", reason="down", findings=[], now=1000
    )

    assert heal_store.pending_actions(tmp_path, now=1001) == {"restart-gateway"}
    assert heal_store.pending_actions(tmp_path, now=1600) == set()


def test_reject_removes_the_action_from_pending(tmp_path: Path) -> None:
    proposal = heal_store.create_proposal(
        tmp_path, action="restart-gateway", reason="down", findings=[], now=1000
    )

    heal_store.reject_proposal(tmp_path, proposal["id"], now=1002)

    assert heal_store.pending_actions(tmp_path, now=1003) == set()


def test_reject_never_executes_and_is_audited(tmp_path: Path) -> None:
    proposal = heal_store.create_proposal(
        tmp_path, action="restart-gateway", reason="down", findings=[], now=1000
    )

    rejected = heal_store.reject_proposal(tmp_path, proposal["id"], now=1001)

    assert rejected is not None and rejected["status"] == "rejected"
    events = [entry["event"] for entry in _audit_events(tmp_path)]
    assert events == ["proposal.created", "proposal.rejected"]


def test_approve_executes_and_records_the_full_audit_chain(tmp_path: Path) -> None:
    proposal = heal_store.create_proposal(
        tmp_path, action="restart-gateway", reason="down", findings=[], now=1000
    )
    calls: list[str] = []

    code, updated = heal_store.approve_and_execute(
        tmp_path,
        proposal["id"],
        allowed_actions={"restart-gateway"},
        execute=lambda action: calls.append(action) or 0,
        now=1001,
    )

    assert code == 0
    assert calls == ["restart-gateway"]
    assert updated is not None and updated["status"] == "executed"
    events = _audit_events(tmp_path)
    assert [entry["event"] for entry in events] == [
        "proposal.created",
        "proposal.approved",
        "proposal.executed",
    ]
    assert all(entry["rollback"] for entry in events[1:])


def test_expired_proposal_is_not_executed(tmp_path: Path) -> None:
    proposal = heal_store.create_proposal(
        tmp_path, action="restart-gateway", reason="down", findings=[], now=1000
    )
    calls: list[str] = []

    code, updated = heal_store.approve_and_execute(
        tmp_path,
        proposal["id"],
        allowed_actions={"restart-gateway"},
        execute=lambda action: calls.append(action) or 0,
        now=1600,
    )

    assert code == 1
    assert calls == []
    assert updated is not None and updated["status"] == "expired"
    assert _audit_events(tmp_path)[-1]["event"] == "proposal.expired"


def test_stale_proposal_is_refused_when_the_action_left_the_diagnosis(
    tmp_path: Path,
) -> None:
    proposal = heal_store.create_proposal(
        tmp_path, action="restart-gateway", reason="down", findings=[], now=1000
    )
    calls: list[str] = []

    code, updated = heal_store.approve_and_execute(
        tmp_path,
        proposal["id"],
        allowed_actions=set(),
        execute=lambda action: calls.append(action) or 0,
        now=1001,
    )

    assert code == 1
    assert calls == []
    assert updated is not None and updated["status"] == "stale"
    assert _audit_events(tmp_path)[-1]["event"] == "proposal.stale"


def test_failed_execution_is_closed_as_failed_and_audited(tmp_path: Path) -> None:
    proposal = heal_store.create_proposal(
        tmp_path, action="restart-gateway", reason="down", findings=[], now=1000
    )

    code, updated = heal_store.approve_and_execute(
        tmp_path,
        proposal["id"],
        allowed_actions={"restart-gateway"},
        execute=lambda action: 7,
        now=1001,
    )

    assert code == 7
    assert updated is not None and updated["status"] == "failed"
    assert updated["returncode"] == 7
    assert _audit_events(tmp_path)[-1]["result"] == "failed (7)"


def test_invalid_proposal_ids_cannot_escape_the_proposal_directory(tmp_path: Path) -> None:
    assert heal_store.load_proposal(tmp_path, "../../state.db") is None
    assert heal_store.load_proposal(tmp_path, "not-a-hex-id") is None
