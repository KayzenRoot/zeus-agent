#!/usr/bin/env python3
"""Zeus Agent home backup/restore (M14, issue #19).

Snapshot a Hermes/Zeus home directory into a single zip with sqlite-safe
database copies (the backup API, not raw file copies of live WAL databases),
skipping volatile caches, with optional retention cleanup. ``--restore``
unpacks an archive back over a home path.

The archive contains ``.env`` and stored credentials when present — treat the
backup file itself as a secret: keep it off shared storage.
"""

from __future__ import annotations

import argparse
import datetime as dt
import shutil
import sqlite3
import sys
import zipfile
from pathlib import Path

VOLATILE_DIRS = {"audio_cache", "image_cache", "cache", "node_modules", "__pycache__"}
DB_EXTENSIONS = {".db"}
SNAPSHOT_NAME = "zeus-home-backup"


def _safe_db_copy(src: Path, dest_dir: Path) -> str:
    """Copy a (possibly live) sqlite database through the backup API.

    Returns the relative name used inside the archive. A ``-wal``/``-shm`` side
    file is not copied: the API produces a consistent single-file snapshot.
    """
    rel = src.name
    dest_dir.mkdir(parents=True, exist_ok=True)
    target = dest_dir / rel
    if src.stat().st_size == 0:
        shutil.copy2(src, target)
        return rel
    conn = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
    try:
        backup = sqlite3.connect(target)
        try:
            src_conn = conn
            src_conn.backup(backup)
        finally:
            backup.close()
    finally:
        conn.close()
    return rel


def create_backup(home: Path, out_dir: Path, label: str = "") -> Path:
    if not home.is_dir():
        raise SystemExit(f"home not found: {home}")
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    suffix = f"-{label}" if label else ""
    archive = out_dir / f"{SNAPSHOT_NAME}-{stamp}{suffix}.zip"
    out_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for entry in sorted(home.rglob("*")):
            rel = entry.relative_to(home)
            if any(part in VOLATILE_DIRS for part in rel.parts):
                continue
            if entry.is_dir():
                continue
            if entry.suffix.lower() in DB_EXTENSIONS:
                arcname = str(Path("dbs") / entry.relative_to(home))
                _safe_db_copy(entry, (out_dir / f".tmp-{stamp}") / Path(arcname).parent)
                tmp_file = (out_dir / f".tmp-{stamp}") / arcname
                zf.write(tmp_file, arcname)
            else:
                zf.write(entry, str(rel))
    shutil.rmtree(out_dir / f".tmp-{stamp}", ignore_errors=True)
    print(f"backup: {archive} ({archive.stat().st_size} bytes)")
    return archive


def restore_backup(archive: Path, home: Path, assume_yes: bool = False) -> None:
    if not archive.is_file():
        raise SystemExit(f"archive not found: {archive}")
    if home.exists() and any(home.iterdir()) and not assume_yes:
        print(f"WARNING: {home} exists and is not empty — its contents will be merged/overwritten.")
        answer = input("continue? [y/N] ").strip().lower()
        if answer != "y":
            raise SystemExit("restore aborted")
    home.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        for member in zf.infolist():
            target = home / member.filename
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if member.filename.startswith("dbs/") and member.filename.endswith(tuple(DB_EXTENSIONS)):
                # Restore through the sqlite API too: a live target with WAL
                # state must not be clobbered by a raw rename.
                target.parent.mkdir(parents=True, exist_ok=True)
                extracted = zf.extract(member, home / ".restore-tmp")
                src_conn = sqlite3.connect(extracted)
                try:
                    dst = sqlite3.connect(target)
                    try:
                        src_conn.backup(dst)
                    finally:
                        dst.close()
                finally:
                    src_conn.close()
                shutil.rmtree(home / ".restore-tmp", ignore_errors=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as payload, open(target, "wb") as out:
                shutil.copyfileobj(payload, out)
    print(f"restore: {archive} -> {home}")


def prune_backups(out_dir: Path, retention_days: int) -> int:
    cutoff = dt.datetime.now() - dt.timedelta(days=retention_days)
    removed = 0
    for candidate in out_dir.glob(f"{SNAPSHOT_NAME}-*.zip"):
        mtime = dt.datetime.fromtimestamp(candidate.stat().st_mtime)
        if mtime < cutoff:
            candidate.unlink()
            removed += 1
    print(f"retention: removed {removed} archive(s) older than {retention_days} days")
    return removed


def main() -> None:
    parser = argparse.ArgumentParser(description="Zeus Agent home backup/restore")
    parser.add_argument("--home", default=str(Path.home() / ".hermes"), help="agent home directory")
    parser.add_argument("--out", default=str(Path.home() / "zeus-backups"), help="backup output directory")
    parser.add_argument("--label", default="", help="optional label in the archive name")
    parser.add_argument("--retention-days", type=int, default=30, help="delete archives older than this")
    parser.add_argument("--restore", metavar="ARCHIVE", help="restore this archive into --home instead of backing up")
    parser.add_argument("--yes", action="store_true", help="skip the restore confirmation (automation)")
    args = parser.parse_args()

    home, out_dir = Path(args.home).expanduser(), Path(args.out).expanduser()
    if args.restore:
        restore_backup(Path(args.restore).expanduser(), home, assume_yes=args.yes)
        return
    archive = create_backup(home, out_dir, args.label)
    prune_backups(out_dir, args.retention_days)
    if archive.exists() and archive.stat().st_size == 0:
        raise SystemExit("backup produced an empty archive")


if __name__ == "__main__":
    sys.exit(main())
