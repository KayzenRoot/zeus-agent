"""Owner review for agent-generated skill writes staged by ``skills.write_approval``.

The agent may propose skill creates/edits/patches; this command lists them, renders the exact diff
the approval would commit, and only applies one after an interactive owner types ``APPROVE``.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from hermes_cli.write_approval_commands import handle_pending_subcommand
from tools import write_approval as wa

APPROVAL_WORD = "APPROVE"


def pending_records() -> list[dict[str, Any]]:
    return [
        {
            "id": record.get("id"),
            "action": record.get("action"),
            "summary": record.get("summary"),
            "origin": record.get("origin"),
            "created_at": record.get("created_at"),
        }
        for record in wa.list_pending(wa.SKILLS)
    ]


def pending_diff(proposal_id: str) -> str | None:
    record = wa.get_pending(wa.SKILLS, proposal_id)
    if record is None:
        return None
    return wa.skill_pending_diff(record)


def reject_pending(proposal_id: str) -> tuple[int, str]:
    if wa.get_pending(wa.SKILLS, proposal_id) is None:
        return 1, f"No pending skill write with id '{proposal_id}'."
    output = handle_pending_subcommand(wa.SKILLS, ["reject", proposal_id]) or ""
    return (0 if output.startswith("Rejected") else 1), output


def approve_pending(proposal_id: str) -> tuple[int, str]:
    record = wa.get_pending(wa.SKILLS, proposal_id)
    if record is None:
        return 1, f"No pending skill write with id '{proposal_id}'."
    if not sys.stdin.isatty():
        return 2, (
            "Owner approval requires an interactive terminal. "
            f"Run `zeus skills review approve {proposal_id}` yourself and type {APPROVAL_WORD}."
        )
    print(f"Pending skill write: {record.get('summary') or record.get('action')}")
    print(f"Review the exact diff with `zeus skills review diff {proposal_id}` before approving.")
    answer = input(f"Type {APPROVAL_WORD} to apply: ").strip()
    if answer != APPROVAL_WORD:
        return 1, "Not approved; nothing was written."
    output = handle_pending_subcommand(wa.SKILLS, ["approve", proposal_id]) or ""
    return (0 if output.startswith("Approved 1") else 1), output


def cmd_review(args) -> int:
    action = getattr(args, "review_action", None)
    if action in {None, "list"}:
        records = pending_records()
        if getattr(args, "json", False):
            print(json.dumps(records, ensure_ascii=False))
        elif not records:
            print("No pending skill writes.")
        else:
            print(f"Pending skill writes ({len(records)}):")
            for record in records:
                origin = " [auto]" if record.get("origin") == "background_review" else ""
                print(f"- {record['id']}{origin}: {record.get('summary') or record.get('action')}")
            print("Review: zeus skills review diff <id>   Approve: ... approve <id>   Reject: ... reject <id>")
        return 0
    if action == "diff":
        diff = pending_diff(args.proposal_id)
        if diff is None:
            print(f"No pending skill write with id '{args.proposal_id}'.")
            return 1
        print(diff)
        return 0
    if action == "approve":
        code, output = approve_pending(args.proposal_id)
        print(output)
        return code
    if action == "reject":
        code, output = reject_pending(args.proposal_id)
        print(output)
        return code
    print(f"Unknown review action: {action}")
    return 1
