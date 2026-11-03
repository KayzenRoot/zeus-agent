"""`hermes entitlement` — activate and inspect the Zeus subscription on this device."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any


def _status_line(status: Any) -> str:
    if not status.active:
        return f"Zeus entitlement inactive ({status.reason})."
    expiry = (
        datetime.fromtimestamp(status.expires_at, tz=UTC).isoformat()
        if status.expires_at
        else "n/a"
    )
    return f"Zeus entitlement active — plan {status.plan or 'n/a'}, expires {expiry}."


def cmd_status(args) -> int:
    import zeus_entitlement

    status = zeus_entitlement.status()
    if getattr(args, "json", False):
        print(json.dumps(status.as_dict()))
    else:
        print(_status_line(status))
    return 0 if status.active else 1


def cmd_activate(args) -> int:
    import zeus_entitlement

    try:
        status = zeus_entitlement.activate_with_code(args.code)
    except zeus_entitlement.EntitlementError as error:
        print(f"Activation failed: {error}")
        return 1
    print(_status_line(status))
    return 0


def cmd_device_id(_args) -> int:
    import zeus_entitlement

    print(zeus_entitlement.local_device_id())
    return 0


def build_parser(subparsers):
    parser = subparsers.add_parser(
        "entitlement",
        help="Manage the Zeus subscription on this device.",
    )
    commands = parser.add_subparsers(dest="entitlement_command", required=True)

    status = commands.add_parser("status", help="Show the local entitlement.")
    status.add_argument("--json", action="store_true", help="Print machine-readable status.")
    status.set_defaults(func=cmd_status)

    activate = commands.add_parser(
        "activate",
        help="Exchange a one-time activation code from the Zeus site.",
    )
    activate.add_argument("code")
    activate.set_defaults(func=cmd_activate)

    device = commands.add_parser("device-id", help="Print this device's activation id.")
    device.set_defaults(func=cmd_device_id)
    return parser
