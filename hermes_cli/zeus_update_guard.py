"""Fail-closed update admission for a Zeus-branded source checkout.

The fork imports the Hermes core for compatibility, but its updater remains
configured for upstream releases, signing and fork-sync. No automatic update
is safe until Zeus has a reviewed publisher, release feed and rollback path.
Only disables source update flows for a checkout carrying ZEUS-001 markers.
"""
from pathlib import Path


def is_zeus_checkout(root: Path) -> bool:
    root = Path(root)
    return ((root / ".zeus" / "brand" / "zeus-mark.svg").is_file()
            and (root / ".zeus" / "docs" / "work-orders" / "ZEUS-001.md").is_file())


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
