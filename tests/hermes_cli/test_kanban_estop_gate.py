"""Behaviour contracts: every kanban dispatcher entry point honours `hermes pause`.

The gateway's embedded tick already gated spawning on the emergency stop, but the
CLI one-shot (`hermes kanban dispatch`) and the standalone daemon loop did not —
an operator could keep spawning new workers while the global pause was engaged.
In-flight workers must never be touched by the gate.
"""
from __future__ import annotations

import argparse
import json
import threading
import time
from pathlib import Path

import pytest

from hermes_cli import kanban_db as kb
from hermes_cli import kanban_db_dispatch as kbd


@pytest.fixture
def kanban_home(tmp_path, monkeypatch):
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    kb.init_db()
    return home


def _paused(monkeypatch, reason: str = "operator drill") -> None:
    from agent import estop

    monkeypatch.setattr(estop, "is_engaged", lambda: True)
    monkeypatch.setattr(estop, "get_state", lambda: {"reason": reason})
    monkeypatch.setattr(estop, "paused_reply", lambda: f"⏸️ Hermes is paused ({reason}).")


def _dispatch_args(**overrides) -> argparse.Namespace:
    values = dict(dry_run=True, max=None, failure_limit=2, json=False)
    values.update(overrides)
    return argparse.Namespace(**values)


def test_cli_dispatch_skips_while_paused(kanban_home, monkeypatch, capsys):
    from hermes_cli.kanban_ops import _cmd_dispatch

    _paused(monkeypatch)
    calls: list[int] = []
    monkeypatch.setattr(kbd, "dispatch_once",
                        lambda *a, **k: calls.append(1) or kb.DispatchResult())

    assert _cmd_dispatch(_dispatch_args()) == 0
    assert calls == []
    out = capsys.readouterr().out
    assert "paused" in out.lower()
    assert "hermes resume" in out


def test_cli_dispatch_json_reports_the_pause(kanban_home, monkeypatch, capsys):
    from hermes_cli.kanban_ops import _cmd_dispatch

    _paused(monkeypatch, "deploy window")
    monkeypatch.setattr(kbd, "dispatch_once", lambda *a, **k: kb.DispatchResult())

    assert _cmd_dispatch(_dispatch_args(json=True)) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"paused": True, "reason": "deploy window", "spawned": []}


def test_cli_dispatch_still_runs_when_not_paused(kanban_home, monkeypatch):
    from agent import estop
    from hermes_cli.kanban_ops import _cmd_dispatch

    monkeypatch.setattr(estop, "is_engaged", lambda: False)
    calls: list[int] = []

    def fake_dispatch_once(*args, **kwargs):
        calls.append(1)
        return kb.DispatchResult()

    monkeypatch.setattr(kbd, "dispatch_once", fake_dispatch_once)
    monkeypatch.setattr(kbd, "configured_max_in_progress", lambda: None)

    assert _cmd_dispatch(_dispatch_args()) == 0
    assert calls == [1]


def test_standalone_daemon_skips_ticks_while_paused(kanban_home, monkeypatch):
    _paused(monkeypatch)
    calls: list[int] = []
    monkeypatch.setattr(kbd, "dispatch_once",
                        lambda *a, **k: calls.append(1) or kb.DispatchResult())
    stop = threading.Event()
    timer = threading.Timer(0.2, stop.set)
    timer.start()
    try:
        kbd.run_daemon(interval=0.02, stop_event=stop)
    finally:
        timer.cancel()
    assert calls == [], "a paused daemon must not dispatch any tick"


def test_standalone_daemon_resumes_after_the_pause_lifts(kanban_home, monkeypatch):
    from agent import estop

    monkeypatch.setattr(estop, "is_engaged", lambda: False)
    stop = threading.Event()
    calls: list[int] = []

    def fake_dispatch_once(*args, **kwargs):
        calls.append(1)
        stop.set()
        return kb.DispatchResult()

    monkeypatch.setattr(kbd, "dispatch_once", fake_dispatch_once)
    monkeypatch.setattr(kbd, "configured_max_in_progress", lambda: None)

    kbd.run_daemon(interval=0.01, stop_event=stop)
    assert calls == [1]
