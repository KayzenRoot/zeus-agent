"""Cron delivery output is user-scoped: created 0600 on POSIX, content intact."""
from __future__ import annotations

import stat
import sys

from gateway.delivery import _write_private_text


def test_private_text_is_written_with_user_only_mode(tmp_path):
    path = tmp_path / "cron-output.md"
    _write_private_text(path, "# output\nsecret-bearing content\n")
    assert path.read_text(encoding="utf-8") == "# output\nsecret-bearing content\n"
    if sys.platform != "win32":
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
