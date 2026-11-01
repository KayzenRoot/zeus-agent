"""Conflicts that a declared ``[tool.uv] override-dependencies`` entry resolves.

An override exists for graphs upstream metadata makes unsatisfiable — here, a
security floor above an exact pin (``pillow>=13,<14`` over
``browser-harness``'s ``pillow==12.3.0``). ``uv pip check`` reads installed
metadata only, so it reports that resolved conflict as a failure and a fresh
environment can never validate.

Tolerance is deliberately narrow and fail-closed: a conflict line counts only
when its subject package is named in an override AND the installed version
satisfies that override's specifier. Any other line in the check output, an
unparseable format, a count mismatch, or a non-numeric/pre-release version
keeps the original failure.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Mapping

# ``uv pip check`` failure line:
#   The package `browser-harness` requires `pillow==12.3.0`, but `13.0.0` is installed
_REQUIRES_RE = re.compile(
    r"requires\s+`(?P<requirement>[^`]+)`\s*,\s*but\s+`(?P<installed>[^`]+)`\s+is installed",
    re.IGNORECASE,
)
# PEP 508 subset sufficient for override entries: name, optional extras, specifier.
_OVERRIDE_RE = re.compile(r"^\s*(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)\s*(?:\[[^\]]*\])?\s*(?P<spec>.*?)\s*$")
_CLAUSE_RE = re.compile(r"^(?P<op>===|==|!=|~=|>=|<=|>|<)\s*(?P<version>\S+)$")
_CLAUSE_SPLIT_RE = re.compile(r",")
_SUMMARY_RE = re.compile(r"^Found\s+\d+\s+incompatibilit", re.IGNORECASE)
# uv's own preamble: ``Using Python 3.14.7 environment at: <path>``.
_PREAMBLE_RE = re.compile(r"^Using Python \S+ environment at: ", re.IGNORECASE)
_VERSION_RE = re.compile(r"^(\d+(?:\.\d+)*)$")
_WILDCARD_RE = re.compile(r"^(\d+(?:\.\d+)*)\.\*$")


def normalize_name(name: str) -> str:
    """PEP 503 normalization, so ``Pillow`` and ``pillow`` share one key."""
    return re.sub(r"[-_.]+", "-", name.strip()).lower()


def declared_overrides(source: Path) -> dict[str, str]:
    """``[tool.uv] override-dependencies`` as normalized name -> specifier.

    Entries that are URLs, paths, or bare names carry no verifiable range and are
    omitted, so a conflict they might explain still fails closed.
    """
    import tomllib

    manifest = Path(source) / "pyproject.toml"
    try:
        data = tomllib.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    entries = (data.get("tool") or {}).get("uv", {}).get("override-dependencies") or []
    overrides: dict[str, str] = {}
    if not isinstance(entries, list):
        return overrides
    for entry in entries:
        if not isinstance(entry, str):
            continue
        requirement = entry.split(";", 1)[0].strip()
        match = _OVERRIDE_RE.match(requirement)
        if not match:
            continue
        specifier = match.group("spec")
        # A URL/path override (``name @ https://…``) carries no verifiable range.
        if not specifier or specifier.startswith("@"):
            continue
        overrides.setdefault(normalize_name(match.group("name")), specifier)
    return overrides


def _release(text: str) -> tuple[int, ...] | None:
    """Strict release tuple, or None for anything with a suffix/wildcard/whitespace."""
    match = _VERSION_RE.match(text.strip())
    if not match:
        return None
    return tuple(int(part) for part in match.group(1).split("."))


def _pad(value: tuple[int, ...], width: int) -> tuple[int, ...]:
    return value + (0,) * (width - len(value))


def _ordered(version: tuple[int, ...], target: tuple[int, ...]) -> int:
    width = max(len(version), len(target))
    left, right = _pad(version, width), _pad(target, width)
    return (left > right) - (left < right)


def _satisfies_clause(version: tuple[int, ...], clause: str) -> bool:
    match = _CLAUSE_RE.match(clause.strip())
    if not match:
        return False
    op, wanted = match.group("op"), match.group("version")

    if op in ("==", "!=") and wanted.endswith(".*"):
        wildcard = _WILDCARD_RE.match(wanted)
        if not wildcard:
            return False
        prefix = tuple(int(part) for part in wildcard.group(1).split("."))
        matches = _ordered(version[: len(prefix)], prefix) == 0 and len(version) >= len(prefix)
        return matches if op == "==" else not matches

    target = _release(wanted)
    if target is None:
        return False

    if op == "~=":
        if len(target) < 2:
            return False
        upper = target[:-1] + (target[-2] + 1,)
        return _ordered(version, target) >= 0 and _ordered(version, upper) < 0
    if op == "==":
        return _ordered(version, target) == 0
    if op == "!=":
        return _ordered(version, target) != 0
    if op == ">=":
        return _ordered(version, target) >= 0
    if op == "<=":
        return _ordered(version, target) <= 0
    if op == ">":
        return _ordered(version, target) > 0
    if op == "<":
        return _ordered(version, target) < 0
    return False


def version_satisfies(version: str, specifier: str) -> bool:
    """True only when every comma-separated clause holds; anything exotic is False."""
    release = _release(version)
    if release is None:
        return False
    clauses = [clause for clause in _CLAUSE_SPLIT_RE.split(specifier) if clause.strip()]
    if not clauses:
        return False
    return all(_satisfies_clause(release, clause) for clause in clauses)


def explained_conflict(line: str, overrides: Mapping[str, str]) -> bool:
    """True when this ``pip check`` line is the conflict an override resolves."""
    match = _REQUIRES_RE.search(line)
    if not match:
        return False
    requirement = _OVERRIDE_RE.match(match.group("requirement"))
    if not requirement:
        return False
    override = overrides.get(normalize_name(requirement.group("name")))
    if override is None:
        return False
    return version_satisfies(match.group("installed"), override)


def tolerated_conflicts(output: str, overrides: Mapping[str, str]) -> list[str]:
    """Every conflict line, but only if ALL of them are explained by an override.

    Returns ``[]`` — keep the failure — for an unparseable output, a count that
    disagrees with the lines seen, or any line that is not a tolerated conflict.
    """
    if not overrides:
        return []
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    conflicts = [line for line in lines if _REQUIRES_RE.search(line)]
    summaries = [line for line in lines if _SUMMARY_RE.match(line)]
    if len(summaries) != 1 or not conflicts:
        return []
    expected = int(re.search(r"\d+", summaries[0]).group(0))
    if len(conflicts) != expected:
        return []
    tolerated: list[str] = []
    for line in lines:
        if _SUMMARY_RE.match(line) or _PREAMBLE_RE.match(line) or line.startswith("Checked "):
            continue
        if line not in conflicts or not explained_conflict(line, overrides):
            return []
        tolerated.append(line)
    return tolerated


__all__ = [
    "declared_overrides",
    "explained_conflict",
    "normalize_name",
    "tolerated_conflicts",
    "version_satisfies",
]
