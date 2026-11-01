"""zeus_backup.py: sqlite-safe snapshot, volatile exclusion, restore round-trip (M14/#19)."""

import sqlite3
import zipfile
from pathlib import Path

import pytest

sys_path = str(Path(__file__).resolve().parents[2] / "scripts")


@pytest.fixture()
def synthetic_home(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    (home / "sessions").mkdir(parents=True)
    (home / "audio_cache").mkdir()
    (home / "skills" / "demo").mkdir(parents=True)
    (home / "config.yaml").write_text("provider: deepseek\n", encoding="utf-8")
    (home / "SOUL.md").write_text("zeus", encoding="utf-8")
    (home / ".env").write_text("DEEPSEEK_API_KEY=fake-key-not-real\n", encoding="utf-8")
    (home / "sessions" / "sess-1.json").write_text("{}", encoding="utf-8")
    (home / "skills" / "demo" / "SKILL.md").write_text("demo", encoding="utf-8")
    (home / "audio_cache" / "volatile.wav").write_bytes(b"\x00" * 16)
    conn = sqlite3.connect(home / "state.db")
    try:
        conn.execute("CREATE TABLE t (id TEXT PRIMARY KEY, v TEXT)")
        conn.execute("INSERT INTO t VALUES ('a', '1')")
        conn.commit()
    finally:
        conn.close()
    return home


def _run(*args: str) -> None:
    import runpy
    import sys

    argv, sys.argv = sys.argv, ["zeus_backup.py", *args]
    try:
        runpy.run_path(sys_path + "/zeus_backup.py", run_name="__main__")
    except SystemExit as exc:  # argparse/main exits
        if exc.code not in (None, 0):
            raise
    finally:
        sys.argv = argv


def test_backup_excludes_volatile_and_includes_state(synthetic_home: Path, tmp_path: Path) -> None:
    out = tmp_path / "backups"
    _run("--home", str(synthetic_home), "--out", str(out), "--retention-days", "30")
    archives = list(out.glob("zeus-home-backup-*.zip"))
    assert len(archives) == 1
    with zipfile.ZipFile(archives[0]) as zf:
        names = set(zf.namelist())
    assert "config.yaml" in names
    assert "SOUL.md" in names
    assert ".env" in names  # included on purpose: the archive is credential-bearing
    assert "sessions/sess-1.json" in names
    assert "skills/demo/SKILL.md" in names
    assert "dbs/state.db" in names
    assert not any("audio_cache" in n for n in names)  # volatile cache excluded
    assert not any(n.endswith("-wal") or n.endswith("-shm") for n in names)


def test_backup_db_is_queryable_and_restore_round_trips(synthetic_home: Path, tmp_path: Path) -> None:
    out = tmp_path / "backups"
    _run("--home", str(synthetic_home), "--out", str(out))
    archive = next(out.glob("zeus-home-backup-*.zip"))

    # The snapshot must be a consistent single-file db: queryable with the row.
    with zipfile.ZipFile(archive) as zf:
        zf.extract("dbs/state.db", tmp_path / "extracted")
    conn = sqlite3.connect(tmp_path / "extracted" / "dbs" / "state.db")
    try:
        rows = conn.execute("SELECT id, v FROM t").fetchall()
    finally:
        conn.close()
    assert rows == [("a", "1")]

    # Restore into an empty target reproduces the live state (--yes: automation path).
    target = tmp_path / "restored"
    (target / "sessions").mkdir(parents=True)
    _run("--restore", str(archive), "--home", str(target), "--yes")
    assert (target / "config.yaml").read_text(encoding="utf-8") == "provider: deepseek\n"
    assert (target / "sessions" / "sess-1.json").exists()
    assert not (target / "audio_cache").exists()  # volatile dirs do not resurrect
    conn = sqlite3.connect(target / "dbs" / "state.db")
    try:
        assert conn.execute("SELECT v FROM t WHERE id='a'").fetchone() == ("1",)
    finally:
        conn.close()


def test_retention_prunes_old_archives(synthetic_home: Path, tmp_path: Path) -> None:
    import os
    import time

    out = tmp_path / "backups"
    _run("--home", str(synthetic_home), "--out", str(out), "--retention-days", "30")
    archive = next(out.glob("zeus-home-backup-*.zip"))
    old = time.time() - 31 * 86_400
    os.utime(archive, (old, old))
    _run("--home", str(synthetic_home), "--out", str(out), "--retention-days", "30", "--label", "second")
    assert not archive.exists()
    assert len(list(out.glob("zeus-home-backup-*.zip"))) == 1  # the fresh one
