"""Owner-approved, deterministic self-healing for the local Zeus runtime.

`zeus heal` never changes anything on its own. It diagnoses, proposes a plan,
and refuses to apply a fix unless the owner runs it in an interactive terminal
and types the approval word. Every applied action is appended to an audit log.
"""

from __future__ import annotations

import json
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

from hermes_cli import heal_store
from hermes_cli.config import get_hermes_home

APPROVAL_WORD = heal_store.APPROVAL_WORD
MIN_FREE_GB = 2.0
STUCK_AFTER_SECONDS = 900
TOOL_FAILURE_WINDOW_SECONDS = 1800
TOOL_FAILURE_THRESHOLD = 3
_TOOL_FAILURE = re.compile(
    r"^(?:Error\b|Traceback \(most recent call last\)|Exception\b|Tool .* failed\b|.* timed out\b)",
    re.IGNORECASE,
)


def _gateway_snapshot() -> tuple[dict[str, Any] | None, bool]:
    from gateway.status import read_runtime_status, runtime_status_pid_is_live

    record = read_runtime_status()
    return record, bool(record and runtime_status_pid_is_live(record))


def _state_db_finding(home: Path) -> dict[str, Any] | None:
    path = home / "state.db"
    if not path.exists():
        return None
    try:
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            result = connection.execute("PRAGMA quick_check").fetchone()
        finally:
            connection.close()
    except sqlite3.Error as error:
        return {
            "code": "state-db-unreadable",
            "severity": "high",
            "summary": f"state.db could not be opened: {error}",
            "action": None,
        }
    if result and result[0] != "ok":
        return {
            "code": "state-db-corrupt",
            "severity": "high",
            "summary": "state.db failed SQLite quick_check; do not auto-repair it.",
            "action": None,
        }
    return None


def _runtime_state_findings(home: Path) -> list[dict[str, Any]]:
    """Read-only signals from state.db: stuck turns/workers and repeated tool failures."""
    path = home / "state.db"
    if not path.exists():
        return []
    now = int(time.time())
    try:
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        try:
            findings = _stuck_findings(connection, now)
            findings.extend(_tool_failure_findings(connection, now))
        finally:
            connection.close()
    except sqlite3.Error:
        return []
    return findings


def _stuck_findings(connection: sqlite3.Connection, now: int) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    admissions = connection.execute(
        """
        SELECT sa.target_session_id AS session_id,
               MAX(COALESCE(m.timestamp, s.last_activity_at, s.started_at)) AS last_activity
        FROM session_admissions sa
        JOIN sessions s ON s.id = sa.target_session_id
        LEFT JOIN messages m ON m.session_id = sa.target_session_id
        WHERE sa.status IN ('started', 'unknown')
        GROUP BY sa.target_session_id
        ORDER BY last_activity ASC
        LIMIT 3
        """
    ).fetchall()
    for row in admissions:
        idle = now - int(row["last_activity"] or 0)
        if idle >= STUCK_AFTER_SECONDS:
            findings.append(
                {
                    "code": "stuck-turn",
                    "severity": "medium",
                    "summary": (
                        f"Session {row['session_id']} has an open turn with no activity "
                        f"for {idle // 60} minutes."
                    ),
                    "action": None,
                }
            )
    workers = connection.execute(
        """
        SELECT w.execution_id, w.session_id,
               MAX(COALESCE(m.timestamp, s.last_activity_at, s.started_at)) AS last_activity
        FROM worker_executions w
        JOIN sessions s ON s.id = w.session_id
        LEFT JOIN messages m ON m.session_id = w.session_id
        WHERE w.status IN ('registered', 'running')
        GROUP BY w.execution_id, w.session_id
        ORDER BY last_activity ASC
        LIMIT 3
        """
    ).fetchall()
    for row in workers:
        idle = now - int(row["last_activity"] or 0)
        if idle >= STUCK_AFTER_SECONDS:
            findings.append(
                {
                    "code": "stuck-worker",
                    "severity": "medium",
                    "summary": (
                        f"Worker {row['execution_id']} on session {row['session_id']} "
                        f"has no activity for {idle // 60} minutes."
                    ),
                    "action": None,
                }
            )
    return findings


def _tool_failure_findings(connection: sqlite3.Connection, now: int) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT tool_name, content FROM messages
        WHERE role = 'tool' AND timestamp >= ? AND tool_name IS NOT NULL
          AND content IS NOT NULL
        ORDER BY timestamp DESC LIMIT 200
        """,
        (now - TOOL_FAILURE_WINDOW_SECONDS,),
    ).fetchall()
    failures = Counter(
        str(row["tool_name"])
        for row in rows
        if _TOOL_FAILURE.match(str(row["content"]).lstrip()[:500])
    )
    return [
        {
            "code": "tool-failures-repeated",
            "severity": "medium",
            "summary": (
                f"Tool '{tool}' returned a hard failure {count} times "
                f"in the last {TOOL_FAILURE_WINDOW_SECONDS // 60} minutes."
            ),
            "action": None,
        }
        for tool, count in failures.most_common(3)
        if count >= TOOL_FAILURE_THRESHOLD
    ]


def diagnose() -> dict[str, Any]:
    home = get_hermes_home()
    findings: list[dict[str, Any]] = []
    record, live = _gateway_snapshot()
    if record is None:
        findings.append(
            {
                "code": "gateway-not-running",
                "severity": "medium",
                "summary": "The local gateway is not running.",
                "action": "restart-gateway",
            }
        )
    elif not live:
        findings.append(
            {
                "code": "gateway-stale",
                "severity": "medium",
                "summary": "The gateway status points at a PID that is no longer alive.",
                "action": "restart-gateway",
            }
        )

    db_finding = _state_db_finding(home)
    if db_finding:
        findings.append(db_finding)
    findings.extend(_runtime_state_findings(home))

    try:
        free_gb = shutil.disk_usage(home).free / 1_000_000_000
    except OSError:
        free_gb = None
    if free_gb is not None and free_gb < MIN_FREE_GB:
        findings.append(
            {
                "code": "disk-low",
                "severity": "high",
                "summary": f"Only {free_gb:.1f} GB free in the runtime home.",
                "action": None,
            }
        )

    from zeus_entitlement import status as entitlement_status

    entitlement = entitlement_status()
    if not entitlement.active:
        findings.append(
            {
                "code": "entitlement-inactive",
                "severity": "high",
                "summary": f"Subscription inactive ({entitlement.reason}).",
                "action": None,
            }
        )

    actions = [
        {
            "action": finding["action"],
            "reason": finding["summary"],
            "requires_owner_approval": True,
        }
        for finding in findings
        if finding.get("action")
    ]
    return {
        "home": str(home),
        "gateway_running": bool(record and live),
        "free_gb": round(free_gb, 1) if free_gb is not None else None,
        "entitlement": entitlement.as_dict(),
        "findings": findings,
        "actions": actions,
    }


def _restart_gateway() -> int:
    completed = subprocess.run(
        [sys.executable, "-m", "hermes_cli.main", "gateway", "restart"],
        check=False,
        timeout=120,
    )
    return int(completed.returncode)


def _execute_action(action: str) -> int:
    if action == "restart-gateway":
        return _restart_gateway()
    raise ValueError(f"unsupported action: {action}")


def propose_actions(plan: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Persist one expiring proposal per actionable finding, skipping live duplicates."""
    home = get_hermes_home()
    plan = plan if plan is not None else diagnose()
    already_pending = heal_store.pending_actions(home)
    created = []
    for item in plan["actions"]:
        action = str(item["action"])
        if action in already_pending:
            continue
        findings = [
            finding for finding in plan["findings"] if finding.get("action") == action
        ]
        created.append(
            heal_store.create_proposal(
                home,
                action=action,
                reason=str(item["reason"]),
                findings=findings,
            )
        )
        already_pending.add(action)
    return created


def apply_action(action: str) -> int:
    plan = diagnose()
    recommended = {item["action"] for item in plan["actions"]}
    if action not in recommended:
        print(f"Refusing '{action}': it is not in the current plan.")
        return 1
    if not sys.stdin.isatty():
        print(
            "Owner approval requires an interactive terminal. "
            f"Run `zeus heal apply {action}` yourself and type {APPROVAL_WORD}."
        )
        return 2
    print(f"Zeus will now: {action}")
    print(f"Rollback: {heal_store.rollback_for(action)}")
    print("This changes local runtime state. Ctrl+C cancels.")
    answer = input(f"Type {APPROVAL_WORD} to continue: ").strip()
    if answer != APPROVAL_WORD:
        print("Not approved; nothing was changed.")
        return 1

    home = get_hermes_home()
    try:
        code = _execute_action(action)
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        heal_store.append_audit(
            home,
            "action.applied",
            action=action,
            result=f"error: {error}",
            rollback=heal_store.rollback_for(action),
        )
        print(f"Healing failed: {error}")
        return 1
    result = "ok" if code == 0 else f"failed ({code})"
    heal_store.append_audit(
        home,
        "action.applied",
        action=action,
        result=result,
        returncode=code,
        rollback=heal_store.rollback_for(action),
    )
    print(f"Healing {result}.")
    return 0 if code == 0 else code


def cmd_status(args) -> int:
    plan = diagnose()
    if getattr(args, "json", False):
        print(json.dumps(plan, ensure_ascii=False))
    else:
        print(f"Home: {plan['home']}")
        print(f"Gateway running: {'yes' if plan['gateway_running'] else 'no'}")
        if plan["free_gb"] is not None:
            print(f"Free disk: {plan['free_gb']} GB")
        print(f"Entitlement: {plan['entitlement']['reason']}")
        if not plan["findings"]:
            print("No issues found.")
        for finding in plan["findings"]:
            print(f"- [{finding['severity']}] {finding['code']}: {finding['summary']}")
    return 0 if not any(item["severity"] == "high" for item in plan["findings"]) else 1


def cmd_plan(args) -> int:
    plan = diagnose()
    if getattr(args, "json", False):
        print(json.dumps(plan["actions"], ensure_ascii=False))
    elif not plan["actions"]:
        print("No owner-approved actions are currently proposed.")
    else:
        for item in plan["actions"]:
            print(f"- {item['action']}: {item['reason']} (owner approval required)")
    return 0


def cmd_propose(args) -> int:
    created = propose_actions()
    if getattr(args, "json", False):
        print(json.dumps(created, ensure_ascii=False))
    elif not created:
        print("No new proposals; every current action already has a pending proposal.")
    else:
        for proposal in created:
            print(
                f"- {proposal['id']}: {proposal['action']} "
                f"(expires in {heal_store.PROPOSAL_TTL_SECONDS // 60} minutes)"
            )
    return 0


def cmd_proposals(args) -> int:
    proposals = heal_store.list_proposals(get_hermes_home())
    if getattr(args, "json", False):
        print(json.dumps(proposals, ensure_ascii=False))
    elif not proposals:
        print("No healing proposals.")
    else:
        for proposal in proposals:
            state = "expired" if proposal.get("expired") else proposal.get("status")
            print(f"- {proposal['id']}: {proposal['action']} [{state}]")
    return 0


def cmd_show(args) -> int:
    proposal = heal_store.load_proposal(get_hermes_home(), args.proposal_id)
    if proposal is None:
        print(f"Proposal not found: {args.proposal_id}")
        return 1
    if getattr(args, "json", False):
        print(json.dumps(proposal, ensure_ascii=False))
        return 0
    print(f"Proposal: {proposal['id']}")
    print(f"Action: {proposal['action']}")
    print(f"Reason: {proposal['reason']}")
    print(f"Rollback: {proposal.get('rollback')}")
    print(f"Status: {proposal.get('status')}")
    print(f"Expires: {proposal.get('expires_at')}")
    for finding in proposal.get("findings") or []:
        print(f"- [{finding.get('severity')}] {finding.get('code')}: {finding.get('summary')}")
    return 0


def cmd_approve(args) -> int:
    home = get_hermes_home()
    proposal = heal_store.load_proposal(home, args.proposal_id)
    if proposal is None:
        print(f"Proposal not found: {args.proposal_id}")
        return 1
    if proposal.get("status") != "pending":
        print(f"Proposal is not pending (status: {proposal.get('status')}).")
        return 1
    if not sys.stdin.isatty():
        print(
            "Owner approval requires an interactive terminal. "
            f"Run `zeus heal approve {args.proposal_id}` yourself and type {APPROVAL_WORD}."
        )
        return 2
    print(f"Zeus will now: {proposal['action']}")
    print(f"Reason: {proposal['reason']}")
    print(f"Rollback: {proposal.get('rollback')}")
    print("This changes local runtime state. Ctrl+C cancels.")
    answer = input(f"Type {APPROVAL_WORD} to continue: ").strip()
    if answer != APPROVAL_WORD:
        print("Not approved; nothing was changed.")
        return 1

    plan = diagnose()
    code, updated = heal_store.approve_and_execute(
        home,
        args.proposal_id,
        allowed_actions={item["action"] for item in plan["actions"]},
        execute=_execute_action,
    )
    status = updated.get("status") if updated else "missing"
    print(f"Proposal {args.proposal_id}: {status}.")
    return code


def cmd_reject(args) -> int:
    proposal = heal_store.reject_proposal(get_hermes_home(), args.proposal_id)
    if proposal is None:
        print(f"Proposal not found: {args.proposal_id}")
        return 1
    print(f"Proposal {args.proposal_id}: {proposal.get('status')}.")
    return 0 if proposal.get("status") == "rejected" else 1


def cmd_apply(args) -> int:
    return apply_action(args.action)


def build_parser(subparsers):
    parser = subparsers.add_parser(
        "heal",
        help="Diagnose the local runtime and apply owner-approved fixes.",
    )
    commands = parser.add_subparsers(dest="heal_command", required=True)

    status = commands.add_parser("status", help="Show runtime findings.")
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=cmd_status)

    plan = commands.add_parser("plan", help="Show owner-approval actions.")
    plan.add_argument("--json", action="store_true")
    plan.set_defaults(func=cmd_plan)

    apply = commands.add_parser("apply", help="Apply one action after owner approval.")
    apply.add_argument("action")
    apply.set_defaults(func=cmd_apply)

    propose = commands.add_parser("propose", help="Persist expiring proposals for current actions.")
    propose.add_argument("--json", action="store_true")
    propose.set_defaults(func=cmd_propose)

    proposals = commands.add_parser("proposals", help="List healing proposals.")
    proposals.add_argument("--json", action="store_true")
    proposals.set_defaults(func=cmd_proposals)

    show = commands.add_parser("show", help="Show one proposal, its rollback and signals.")
    show.add_argument("proposal_id")
    show.add_argument("--json", action="store_true")
    show.set_defaults(func=cmd_show)

    approve = commands.add_parser("approve", help="Approve and execute one proposal.")
    approve.add_argument("proposal_id")
    approve.set_defaults(func=cmd_approve)

    reject = commands.add_parser("reject", help="Reject one proposal without executing it.")
    reject.add_argument("proposal_id")
    reject.set_defaults(func=cmd_reject)
    return parser