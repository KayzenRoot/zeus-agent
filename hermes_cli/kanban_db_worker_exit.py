"""Worker exit-status decoding for the kanban dispatcher.

Pure helpers split out of ``kanban_db_dispatch`` (a ratcheted sibling: it may only
shrink). POSIX wait-status encoding does not exist on Windows, so the dispatcher
decodes the raw integer by hand instead of ``os.WIFEXITED``/``os.WTERMSIG``.
"""

from __future__ import annotations

from typing import Optional


def _wait_status_from_returncode(returncode: int) -> int:
    """Encode a ``Popen.returncode`` in the wait-status layout the registry stores."""
    return (int(returncode) & 0xFF) << 8


def classify_exit_code(code: int) -> tuple[str, int]:
    """``(kind, code)`` for a worker's exit code, however it was observed."""
    from hermes_cli import kanban_db as _kb

    if code == 0:
        return ("clean_exit", 0)
    if code == _kb.KANBAN_RATE_LIMIT_EXIT_CODE:
        return ("rate_limited", code)
    if code == _kb.KANBAN_TERMINAL_PROVIDER_EXIT_CODE:
        return ("terminal_provider", code)
    return ("nonzero_exit", code)


def classify_worker_exit(
    pid: int, recent_worker_exits,
) -> tuple[str, Optional[int]]:
    """``(kind, code)`` for a reaped worker PID from the reap registry.

    ``clean_exit`` (rc 0 while still ``running`` = protocol violation),
    ``rate_limited`` (``KANBAN_RATE_LIMIT_EXIT_CODE``, never counts as a failure),
    ``nonzero_exit``, ``signaled`` (``code`` is the signal), ``unknown`` (pid not
    in the reap registry; ``code`` None). Bit-level decode: low 7 bits = signal
    (0 = normal exit, 0x7F = stopped), bits 8-15 = exit code.
    """
    entry = recent_worker_exits.get(int(pid))
    if entry is None:
        return ("unknown", None)
    raw, _ = entry
    raw = int(raw)
    signal_number = raw & 0x7F
    if signal_number == 0:
        return classify_exit_code((raw >> 8) & 0xFF)
    if signal_number != 0x7F:
        return ("signaled", signal_number)
    return ("unknown", None)


__all__ = ["_wait_status_from_returncode", "classify_exit_code", "classify_worker_exit"]
