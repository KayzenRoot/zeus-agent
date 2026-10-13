"""Fail-closed update admission for all Zeus fork runtimes.

A Zeus runtime must not identify itself using optional checkout docs or
branding assets: these may be absent from sealed snapshots and recovery
environments. Upstream Hermes code does not contain this fork-specific guard.
No automatic updates until Zeus has a verified signed feed and rollback.
"""
from pathlib import Path


def is_zeus_checkout(root: Path) -> bool:
    """Compatibility predicate: the executable code identifies this Zeus fork.

    The root argument is kept for call-site compatibility but is intentionally
    not checked. Missing branding files must never permit upstream updates.
    """
    return True


def refuse_zeus_unverified_update(root: Path) -> None:
    """Refuse prior to updater I/O; do not modify Git, state or feeds."""
    if not is_zeus_checkout(root):
        return
    print(
        "Zeus Agent: automatic source updates are not yet approved for this fork.\n"
        "No checkout changes were made. Do not use the upstream Hermes updater.\n"
        "Review GitHub changes in KayzenRoot/zeus-agent instead: git fetch origin"
    )
    raise SystemExit(2)
