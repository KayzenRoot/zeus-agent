"""FTS5 query sanitizer must stay linear on adversarial separator runs (CodeQL py/redos)."""
from __future__ import annotations

import time


def _sanitize(query: str) -> str:
    from hermes_state_search import SessionSearchMixin

    return SessionSearchMixin._sanitize_fts5_query(query)


def test_pathological_separator_run_does_not_backtrack():
    query = "a" + ("_" * 50_000) + "b"
    started = time.perf_counter()
    sanitized = _sanitize(query)
    elapsed = time.perf_counter() - started
    assert isinstance(sanitized, str)
    assert elapsed < 2.0, f"sanitizer took {elapsed:.2f}s on a separator run"


def test_dotted_term_is_still_one_quoted_term():
    assert '"my-app.config.ts"' in _sanitize("my-app.config.ts")
