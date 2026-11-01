"""Behaviour contracts: a declared uv override resolves the pip-check conflict it created.

``[tool.uv] override-dependencies`` can make a graph satisfiable that upstream
metadata pins impossibly (the security-floor case: Pillow 13 over
``browser-harness==0.1.13``'s ``pillow==12.3.0``). ``uv pip check`` does not
read overrides, so those resolved conflicts must be tolerated — and nothing
else may be.
"""
from __future__ import annotations

from pathlib import Path
from subprocess import CompletedProcess

import pytest

from pm.environment import PythonEnvironment
from pm.overrides import (
    declared_overrides,
    explained_conflict,
    tolerated_conflicts,
    version_satisfies,
)
from pm.package import InstallError

CONFLICT = (
    "The package `browser-harness` requires `pillow==12.3.0`, but `13.0.0` is installed"
)
OUTPUT = (
    "Using Python 3.14.7 environment at: C:\\cache\\venv\n"
    "Checked 98 packages in 46ms\nFound 1 incompatibility\n"
    f"{CONFLICT}\n"
)


def _source(tmp_path: Path, entries: list[str]) -> Path:
    quoted = "".join(f'  "{entry}",\n' for entry in entries)
    (tmp_path / "pyproject.toml").write_text(
        f"[project]\nname = 'fixture'\nversion = '0.0.0'\n\n"
        f"[tool.uv]\noverride-dependencies = [\n{quoted}]\n",
        encoding="utf-8",
    )
    return tmp_path


def _environment(tmp_path: Path, monkeypatch, stderr: str = OUTPUT, returncode: int = 1) -> PythonEnvironment:
    environment = PythonEnvironment(
        uv=tmp_path / "uv", python=tmp_path / "python",
        destination=tmp_path / "venv", cache=tmp_path / "cache", env={},
    )
    monkeypatch.setattr(
        PythonEnvironment, "_run",
        lambda self, args, *, cwd, timeout: CompletedProcess(args, returncode, "", stderr),
    )
    return environment


@pytest.mark.parametrize("version, specifier, expected", [
    ("13.0.0", ">=13,<14", True),
    ("12.3.0", ">=13,<14", False),
    ("13.0.0", "==13.0", True),          # release segments pad with zeros
    ("13.0.1", "==13.0", False),
    ("13.1", "~=13.0", True),
    ("14.0", "~=13.0", False),
    ("13.2.1", "~=13.2.0", True),
    ("13.3", "~=13.2.0", False),
    ("13.0.0", "!=12.3.0", True),
    ("13.0.0", "==13.*", True),
    ("13.0.0", "!=13.*", False),
    ("13.0.0rc1", ">=13,<14", False),    # fail closed on non-release versions
    ("13.0.0", "garbage", False),
    ("13.0.0", "", False),
])
def test_version_satisfies_is_strict(version, specifier, expected):
    assert version_satisfies(version, specifier) is expected


def test_explained_conflict_matches_the_package_the_override_names():
    assert explained_conflict(CONFLICT, {"pillow": ">=13,<14"}) is True
    assert explained_conflict(CONFLICT, {"browser-harness": ">=1"}) is False


def test_declared_overrides_read_the_manifest_and_skip_unverifiable_entries(tmp_path):
    source = _source(tmp_path, [
        "pillow>=13,<14",
        "requests @ https://example.test/requests.whl",
        "bare-name",
        "types-foo>=2; python_version >= '3.14'",
    ])
    assert declared_overrides(source) == {"pillow": ">=13,<14", "types-foo": ">=2"}


def test_check_tolerates_a_conflict_the_declared_override_resolves(tmp_path, monkeypatch):
    source = _source(tmp_path, ["pillow>=13,<14"])
    _environment(tmp_path, monkeypatch).check(source)


def test_check_without_a_source_still_fails(tmp_path, monkeypatch):
    with pytest.raises(InstallError, match="dependency validation failed"):
        _environment(tmp_path, monkeypatch).check()


def test_check_rejects_a_conflict_the_override_does_not_cover(tmp_path, monkeypatch):
    source = _source(tmp_path, ["numpy>=2"])
    with pytest.raises(InstallError, match="dependency validation failed"):
        _environment(tmp_path, monkeypatch).check(source)


def test_check_rejects_an_installed_version_outside_the_override_range(tmp_path, monkeypatch):
    source = _source(tmp_path, ["pillow>=14,<15"])
    with pytest.raises(InstallError, match="dependency validation failed"):
        _environment(tmp_path, monkeypatch).check(source)


def test_check_rejects_unrecognised_output_lines(tmp_path, monkeypatch):
    source = _source(tmp_path, ["pillow>=13,<14"])
    stderr = OUTPUT + "something else broke\n"
    with pytest.raises(InstallError, match="dependency validation failed"):
        _environment(tmp_path, monkeypatch, stderr=stderr).check(source)


def test_tolerated_conflicts_requires_a_consistent_count(tmp_path):
    overrides = {"pillow": ">=13,<14"}
    assert tolerated_conflicts(OUTPUT, overrides) == [CONFLICT]
    assert tolerated_conflicts(OUTPUT.replace("Found 1", "Found 2"), overrides) == []
    assert tolerated_conflicts(OUTPUT, {}) == []
