"""Owner-approved, deterministic self-healing for the local Zeus runtime.

`zeus heal` never changes anything on its own. It diagnoses, proposes a plan,
and refuses to apply a fix unless the owner runs it in an interactive terminal
and types the approval word. Every applied action is appended to an audit log.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from hermes_cli.config import get_hermes_home

APPROVAL_WORD = "APPROVE"
MIN_FREE_GB = 2.0


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


def _audit_log(home: Path) -> Path:
    path = home / "logs" / "heal-audit.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _append_audit(home: Path, action: str, result: str, returncode: int | None) -> None:
    path = _audit_log(home)
    entry = {
        "at": int(time.time()),
        "action": action,
        "result": result,
        "returncode": returncode,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    try:
        path.chmod(0o600)
    except OSError:
        pass


def _restart_gateway() -> int:
    completed = subprocess.run(
        [sys.executable, "-m", "hermes_cli.main", "gateway", "restart"],
        check=False,
        timeout=120,
    )
    return int(completed.returncode)


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
    print("This changes local runtime state. Ctrl+C cancels.")
    answer = input(f"Type {APPROVAL_WORD} to continue: ").strip()
    if answer != APPROVAL_WORD:
        print("Not approved; nothing was changed.")
        return 1

    home = get_hermes_home()
    try:
        if action == "restart-gateway":
            code = _restart_gateway()
        else:
            print(f"Unsupported action: {action}")
            return 1
    except (OSError, subprocess.SubprocessError) as error:
        _append_audit(home, action, f"error: {error}", None)
        print(f"Healing failed: {error}")
        return 1
    result = "ok" if code == 0 else f"failed ({code})"
    _append_audit(home, action, result, code)
    print(f"Healing {result}.")
    return 0 if code == 0 else 1


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
    return parser
