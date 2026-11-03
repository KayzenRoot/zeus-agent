"""Persistent, expiring healing proposals and their append-only audit trail.

The agent may diagnose and propose; only an explicit owner approval may execute. Proposals live
under ``<HERMES_HOME>/heal-proposals`` as 0600 JSON files and expire by default after ten minutes.
"""

from __future__ import annotations

import json
import logging
import os
import re
import secrets
import time
from pathlib import Path
from typing import Any, Callable

PROPOSAL_TTL_SECONDS = 600
APPROVAL_WORD = "APPROVE"
_PROPOSAL_ID = re.compile(r"^[0-9a-f]{16}$")
logger = logging.getLogger(__name__)

_ROLLBACKS = {
    "restart-gateway": (
        "Run `zeus gateway restart` again if the restart made things worse, "
        "or `zeus gateway stop` to leave the gateway stopped."
    ),
}


def rollback_for(action: str) -> str:
    return _ROLLBACKS.get(action, "No automated rollback exists for this action.")


def proposal_dir(home: Path) -> Path:
    return home / "heal-proposals"


def audit_log(home: Path) -> Path:
    path = home / "logs" / "heal-audit.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def append_audit(
    home: Path,
    event: str,
    *,
    action: str,
    result: str,
    returncode: int | None = None,
    proposal_id: str | None = None,
    rollback: str | None = None,
    detail: dict[str, Any] | None = None,
) -> None:
    entry: dict[str, Any] = {
        "at": int(time.time()),
        "event": event,
        "action": action,
        "result": result,
        "returncode": returncode,
    }
    if proposal_id is not None:
        entry["proposal_id"] = proposal_id
    if rollback is not None:
        entry["rollback"] = rollback
    if detail:
        entry["detail"] = detail
    path = audit_log(home)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    try:
        path.chmod(0o600)
    except OSError:
        pass


def _write_private(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(4)}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        try:
            path.chmod(0o600)
        except OSError:
            pass
    finally:
        temporary.unlink(missing_ok=True)


def _proposal_path(home: Path, proposal_id: str) -> Path | None:
    if not _PROPOSAL_ID.fullmatch(proposal_id):
        return None
    return proposal_dir(home) / f"{proposal_id}.json"


def create_proposal(
    home: Path,
    *,
    action: str,
    reason: str,
    findings: list[dict[str, Any]],
    now: int | None = None,
) -> dict[str, Any]:
    created_at = int(time.time()) if now is None else int(now)
    proposal = {
        "id": secrets.token_hex(8),
        "action": action,
        "reason": reason,
        "findings": findings,
        "rollback": rollback_for(action),
        "requires_owner_approval": True,
        "status": "pending",
        "created_at": created_at,
        "expires_at": created_at + PROPOSAL_TTL_SECONDS,
    }
    path = _proposal_path(home, proposal["id"])
    assert path is not None
    _write_private(path, proposal)
    append_audit(
        home,
        "proposal.created",
        action=action,
        result="pending",
        proposal_id=proposal["id"],
        rollback=proposal["rollback"],
        detail={
            "reason": reason,
            "signals": [
                str(finding.get("code")) for finding in findings if finding.get("code")
            ],
        },
    )
    return proposal


def load_proposal(home: Path, proposal_id: str) -> dict[str, Any] | None:
    path = _proposal_path(home, proposal_id)
    if path is None or not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def _save(home: Path, proposal: dict[str, Any]) -> None:
    path = _proposal_path(home, str(proposal["id"]))
    if path is None:
        raise ValueError("invalid proposal id")
    _write_private(path, proposal)


def list_proposals(home: Path, *, now: int | None = None) -> list[dict[str, Any]]:
    current = int(time.time()) if now is None else int(now)
    directory = proposal_dir(home)
    if not directory.exists():
        return []
    proposals = []
    for path in directory.glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            continue
        if not isinstance(payload, dict) or not _PROPOSAL_ID.fullmatch(str(payload.get("id") or "")):
            continue
        payload["expired"] = (
            payload.get("status") == "pending" and current >= int(payload.get("expires_at") or 0)
        )
        proposals.append(payload)
    return sorted(proposals, key=lambda item: int(item.get("created_at") or 0), reverse=True)


def pending_actions(home: Path, *, now: int | None = None) -> set[str]:
    return {
        str(proposal["action"])
        for proposal in list_proposals(home, now=now)
        if proposal.get("status") == "pending" and not proposal.get("expired")
    }


def reject_proposal(
    home: Path, proposal_id: str, *, now: int | None = None
) -> dict[str, Any] | None:
    proposal = load_proposal(home, proposal_id)
    if proposal is None or proposal.get("status") != "pending":
        return proposal
    proposal["status"] = "rejected"
    proposal["rejected_at"] = int(time.time()) if now is None else int(now)
    _save(home, proposal)
    append_audit(
        home,
        "proposal.rejected",
        action=str(proposal["action"]),
        result="rejected",
        proposal_id=proposal_id,
        rollback=str(proposal.get("rollback") or ""),
    )
    return proposal


def approve_and_execute(
    home: Path,
    proposal_id: str,
    *,
    allowed_actions: set[str],
    execute: Callable[[str], int],
    now: int | None = None,
) -> tuple[int, dict[str, Any] | None]:
    proposal = load_proposal(home, proposal_id)
    if proposal is None or proposal.get("status") != "pending":
        return 1, proposal
    current = int(time.time()) if now is None else int(now)
    action = str(proposal["action"])
    if current >= int(proposal.get("expires_at") or 0):
        proposal["status"] = "expired"
        proposal["expired_at"] = current
        _save(home, proposal)
        append_audit(
            home,
            "proposal.expired",
            action=action,
            result="expired",
            proposal_id=proposal_id,
        )
        return 1, proposal
    if action not in allowed_actions:
        proposal["status"] = "stale"
        proposal["stale_at"] = current
        _save(home, proposal)
        append_audit(
            home,
            "proposal.stale",
            action=action,
            result="refused: action is no longer in the diagnosis",
            proposal_id=proposal_id,
        )
        return 1, proposal

    proposal["status"] = "approved"
    proposal["approved_at"] = current
    _save(home, proposal)
    append_audit(
        home,
        "proposal.approved",
        action=action,
        result="approved",
        proposal_id=proposal_id,
        rollback=str(proposal.get("rollback") or ""),
    )

    error = ""
    try:
        returncode = int(execute(action))
    except Exception as exc:  # boundary: a failed action must still close the audit trail
        logger.exception("owner-approved healing action raised")
        returncode = 1
        error = str(exc)
    proposal["status"] = "executed" if returncode == 0 else "failed"
    proposal["executed_at"] = int(time.time())
    proposal["returncode"] = returncode
    if error:
        proposal["error"] = error
    _save(home, proposal)
    append_audit(
        home,
        "proposal.executed",
        action=action,
        result=error or ("ok" if returncode == 0 else f"failed ({returncode})"),
        returncode=returncode,
        proposal_id=proposal_id,
        rollback=str(proposal.get("rollback") or ""),
    )
    return returncode, proposal
