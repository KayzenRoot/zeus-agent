#!/usr/bin/env python3
"""Zeus-owned local install (issue #5, flow B).

Installs a *local development/production* Zeus from the verified checkout into an
isolated root: a dedicated ``HERMES_HOME``, a launcher that activates the repo's
own pm environment, and a receipt that uninstall mirrors. It never downloads or
executes an upstream installer, never touches an existing Hermes/Zeus profile,
and never enables the update/bootstrap channels (those stay NO-GO for release C).

    zeus-install --plan            # verify checkout, print actions, write nothing
    zeus-install                   # build the runtime env and install the launcher
    zeus-install --uninstall --yes # remove what the receipt created

Exit codes: 0 ok, 2 refused (zeus-release-unapproved / unsafe target), 1 failed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone, UTC
from pathlib import Path
from typing import Optional

FORBIDDEN_EXIT = 2
PREFIX = "zeus-install:"
RECEIPT_NAME = "receipt.json"
RECEIPT_SCHEMA = 2
# Dependency inputs whose change invalidates the venv baked into the launcher;
# matches pm.environments.ACTIVATION_INPUTS.
DEPENDENCY_INPUTS = ("uv.lock", "pyproject.toml", "pm/lock.json")
ACCEPTED_ORIGINS = (
    "https://github.com/KayzenRoot/zeus-agent.git",
    "https://github.com/KayzenRoot/zeus-agent",
    "git@github.com:KayzenRoot/zeus-agent.git",
)


@dataclass(frozen=True)
class Checkout:
    root: Path
    head: str
    origin: str


def _say(message: str) -> None:
    print(f"{PREFIX} {message}", flush=True)


def _refuse(message: str) -> int:
    print(f"{PREFIX} zeus-release-unapproved: {message}", file=sys.stderr, flush=True)
    return FORBIDDEN_EXIT


def _git(checkout: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(checkout), *args],
        capture_output=True, text=True, timeout=30, check=False,
    )


def verify_checkout(checkout: Path) -> tuple[Optional[Checkout], Optional[str]]:
    """(checkout, None) for a verified fork checkout, else (None, refusal reason)."""
    if not checkout.is_dir():
        return None, f"checkout does not exist: {checkout}"
    if not (checkout / "setup-hermes.sh").is_file():
        return None, f"not a Zeus checkout (setup-hermes.sh missing): {checkout}"
    top = _git(checkout, "rev-parse", "--show-toplevel")
    if top.returncode != 0:
        return None, "not a git checkout — downloaded copies are refused; clone KayzenRoot/zeus-agent"
    if Path(top.stdout.strip()).resolve() != checkout.resolve():
        return None, f"path is not the repository root: {checkout}"
    origin = _git(checkout, "remote", "get-url", "origin")
    if origin.returncode != 0:
        return None, "no origin remote — refusing an untraceable checkout"
    origin_url = origin.stdout.strip()
    if origin_url not in ACCEPTED_ORIGINS:
        return None, f"origin is not KayzenRoot/zeus-agent: {origin_url}"
    head = _git(checkout, "rev-parse", "HEAD")
    if head.returncode != 0:
        return None, "cannot resolve HEAD"
    dirty = _git(checkout, "status", "--porcelain", "--untracked-files=no")
    if dirty.returncode != 0:
        return None, "cannot inspect the working tree"
    if dirty.stdout.strip():
        return None, "tracked files are modified — commit or stash before installing the checkout"
    return Checkout(root=checkout.resolve(), head=head.stdout.strip(), origin=origin_url), None


def default_root() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "ZeusAgent"
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / "zeus-agent"


def validate_root(root: Path, checkout: Checkout) -> Optional[str]:
    resolved = root.expanduser().resolve()
    if resolved == Path(resolved.anchor) or resolved == Path.home().resolve():
        return f"refusing an unsafe install root: {resolved}"
    if checkout.root == resolved or checkout.root in resolved.parents:
        return "install root must live outside the checkout"
    if (resolved / RECEIPT_NAME).exists():
        return f"already installed at {resolved} — run --uninstall first"
    return None


def _setup_command(checkout: Path) -> list[str]:
    if sys.platform == "win32":
        return ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", str(checkout / "setup-hermes.ps1"), "-RuntimeOnly"]
    return ["bash", str(checkout / "setup-hermes.sh"), "--runtime-only"]


def run_setup(checkout: Checkout, home: Path) -> int:
    """Build the runtime environment under the isolated home. The installer itself does no I/O."""
    env = os.environ.copy()
    env["HERMES_HOME"] = str(home)
    _say(f"building the runtime environment under {home} (no upstream installer runs)")
    try:
        return subprocess.run(_setup_command(checkout.root), cwd=str(checkout.root),
                              env=env, timeout=3600, check=False).returncode
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"{PREFIX} setup failed: {exc}", file=sys.stderr, flush=True)
        return 1


def _install_key(checkout: Path) -> str:
    """PM's install key: sha256 of the resolved checkout, truncated (pm.environments)."""
    return hashlib.sha256(str(checkout.resolve()).encode("utf-8")).hexdigest()[:16]


def _recorded_venv(home: Path, checkout: Checkout) -> Optional[Path]:
    """The committed venv from PM's facts.json, read directly (no pm import needed)."""
    facts = home / "installs" / _install_key(checkout.root) / "facts.json"
    try:
        data = json.loads(facts.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    venv = ((data.get("packages") or {}).get("venv") or {}).get("environment")
    if not venv:
        return None
    path = Path(venv)
    return path if path.is_dir() else None


def launcher_target(checkout: Checkout, venv: Optional[Path]) -> Optional[Path]:
    if venv is None:
        return None
    target = venv / ("Scripts/hermes.exe" if sys.platform == "win32" else "bin/hermes")
    return target if target.is_file() else None


def dependency_digests(checkout: Checkout) -> dict[str, str]:
    """SHA-256 of every input that decides the dependency set (launcher freshness gate)."""
    digests: dict[str, str] = {}
    for name in DEPENDENCY_INPUTS:
        path = checkout.root / name
        try:
            digests[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            continue
    return digests


def _ps_quote(value: str) -> str:
    return value.replace("'", "''")


def launcher_paths(root: Path) -> list[Path]:
    if sys.platform == "win32":
        return [root / "zeus.cmd", root / "zeus.ps1"]
    return [root / "bin" / "zeus"]


def write_launchers(root: Path, checkout: Checkout, home: Path, *,
                    target: Optional[Path], digests: dict[str, str]) -> list[Path]:
    """Launchers exec the recorded venv while its dependency inputs are unchanged.

    A changed lock/pyproject/pm-lock (or a vanished target) falls back to the
    checkout's own activation, which re-syncs before running. Every run exports
    the isolated HERMES_HOME; no update/bootstrap channel is enabled.
    """
    created: list[Path] = []
    if sys.platform == "win32":
        (root / "zeus.cmd").write_text(
            '@echo off\r\n'
            'powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0zeus.ps1" %*\r\n',
            encoding="utf-8")
        lines = [
            "# Zeus Agent local launcher — installed by scripts/zeus-install.ps1",
            f"$env:HERMES_HOME = '{_ps_quote(str(home))}'",
        ]
        if target is not None and digests:
            expected = "".join(
                f"    '{_ps_quote(name)}' = '{digest}'\n"
                for name, digest in sorted(digests.items())
            )
            lines += [
                f"$repo = '{_ps_quote(str(checkout.root))}'",
                "$expected = @{",
                expected.rstrip("\n"),
                "}",
                "$fresh = $true",
                "foreach ($name in $expected.Keys) {",
                "    $path = Join-Path $repo $name",
                "    if (-not (Test-Path -LiteralPath $path)) { $fresh = $false; break }",
                "    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLower()",
                "    if ($actual -ne $expected[$name]) { $fresh = $false; break }",
                "}",
                f"$target = '{_ps_quote(str(target))}'",
                "if ($fresh -and (Test-Path -LiteralPath $target)) {",
                "    & $target @args",
                "    exit $LASTEXITCODE",
                "}",
                "# Dependency inputs changed (or the target vanished): re-sync via activation.",
                f". '{_ps_quote(str(checkout.root / 'activate.ps1'))}'",
                "& hermes @args",
                "exit $LASTEXITCODE",
            ]
        else:
            lines += [
                f". '{_ps_quote(str(checkout.root / 'activate.ps1'))}'",
                "& hermes @args",
                "exit $LASTEXITCODE",
            ]
        (root / "zeus.ps1").write_text("\n".join(lines) + "\n", encoding="utf-8")
        created += launcher_paths(root)
    else:
        launcher = root / "bin" / "zeus"
        launcher.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "#!/usr/bin/env bash",
            "# Zeus Agent local launcher — installed by scripts/zeus-install.sh",
            f"export HERMES_HOME={shlex.quote(str(home))}",
        ]
        if target is not None and digests:
            checks = "\n".join(
                f"[ \"$(hash_file {shlex.quote(str(checkout.root / name))})\" = {shlex.quote(digest)} ] || fresh=0"
                for name, digest in sorted(digests.items())
            )
            lines += [
                "hash_file() {",
                "  if command -v sha256sum >/dev/null 2>&1; then sha256sum \"$1\" | cut -d' ' -f1",
                "  else shasum -a 256 \"$1\" | cut -d' ' -f1; fi",
                "}",
                "fresh=1",
                checks,
                f"if [ \"$fresh\" = 1 ] && [ -x {shlex.quote(str(target))} ]; then",
                f"  exec {shlex.quote(str(target))} \"$@\"",
                "fi",
                "# Dependency inputs changed (or the target vanished): re-sync via activation.",
            ]
        lines += [
            f". {shlex.quote(str(checkout.root / 'activate'))}",
            'exec hermes "$@"',
        ]
        launcher.write_text("\n".join(lines) + "\n", encoding="utf-8")
        launcher.chmod(0o755)
        created.append(launcher)
    return created


def write_receipt(root: Path, checkout: Checkout, home: Path, launchers: list[Path], *,
                  target: Optional[Path], digests: dict[str, str]) -> Path:
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "kind": "zeus-local-install",
        "installed_at": datetime.now(UTC).isoformat(),
        "checkout": str(checkout.root),
        "origin": checkout.origin,
        "head": checkout.head,
        "root": str(root),
        "hermes_home": str(home),
        "launchers": [str(path) for path in launchers],
        "launcher_target": str(target) if target is not None else None,
        "dependency_inputs": digests,
        "created_paths": sorted({str(root), str(home)}),
        "release_channel": "local-development",
        "updates_enabled": False,
    }
    path = root / RECEIPT_NAME
    path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return path


def _plan_lines(checkout: Checkout, root: Path) -> list[str]:
    home = root / "home"
    return [
        f"checkout: {checkout.root} @ {checkout.head}",
        f"origin:   {checkout.origin}",
        f"root:     {root}",
        f"home:     {home} (isolated HERMES_HOME; existing profiles are not touched)",
        f"setup:    {' '.join(_setup_command(checkout.root))}",
        f"launcher: {', '.join(str(p) for p in launcher_paths(root))}",
        "network:  none from the installer; the pm build syncs the committed lock only",
        "channels: updates/bootstrap stay disabled (release C is NO-GO)",
    ]


def install(checkout: Checkout, root: Path) -> int:
    root = root.expanduser().resolve()
    reason = validate_root(root, checkout)
    if reason:
        return _refuse(reason)
    home = root / "home"
    created_root = not root.exists()
    root.mkdir(parents=True, exist_ok=True)
    home.mkdir(parents=True, exist_ok=True)
    try:
        if run_setup(checkout, home) != 0:
            raise RuntimeError("setup-hermes failed — see its output above")
        target = launcher_target(checkout, _recorded_venv(home, checkout))
        digests = dependency_digests(checkout)
        launchers = write_launchers(root, checkout, home, target=target, digests=digests)
        write_receipt(root, checkout, home, launchers, target=target, digests=digests)
    except BaseException:
        if created_root:
            shutil.rmtree(root, ignore_errors=True)
        raise
    _say(f"installed Zeus local at {root}")
    _say(f"launch with: {launcher_paths(root)[0]}")
    _say("receipt: " + str(root / RECEIPT_NAME))
    return 0


def uninstall(root: Path, *, confirmed: bool, purge_data: bool) -> int:
    root = root.expanduser().resolve()
    receipt_path = root / RECEIPT_NAME
    if not receipt_path.is_file():
        return _refuse(f"no Zeus local receipt at {root}")
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        return _refuse(f"unreadable receipt: {exc}")
    if receipt.get("kind") != "zeus-local-install":
        return _refuse("receipt does not belong to a Zeus local install")
    home = Path(receipt.get("hermes_home") or root / "home")
    user_data = any((home / name).exists() for name in ("sessions", "memories", "state.db"))
    if not confirmed:
        _say(f"would remove launchers + receipt under {root}")
        _say(f"would {'PURGE' if purge_data else 'keep'} user data at {home}"
             + ("" if purge_data or not user_data else " (sessions/memories present)"))
        _say("re-run with --yes to proceed")
        return 0
    for launcher in receipt.get("launchers") or launcher_paths(root):
        try:
            Path(launcher).unlink(missing_ok=True)
        except OSError as exc:
            print(f"{PREFIX} could not remove launcher {launcher}: {exc}", file=sys.stderr)
    if purge_data:
        shutil.rmtree(home, ignore_errors=True)
    elif user_data:
        _say(f"kept user data at {home} (pass --purge-data to delete it)")
    receipt_path.unlink(missing_ok=True)
    if not purge_data and home.exists() and any(home.iterdir()):
        _say(f"kept {home}; remove it manually once its data is no longer needed")
    elif not purge_data:
        shutil.rmtree(home, ignore_errors=True)
    try:
        root.rmdir()
    except OSError:
        pass
    _say(f"uninstalled Zeus local from {root}")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="zeus-install",
        description="Install Zeus locally from this verified checkout into an isolated root.")
    parser.add_argument("--checkout", default=str(Path(__file__).resolve().parents[1]),
                        help="repository checkout (default: this script's repository)")
    parser.add_argument("--root", default=None,
                        help="install root (default: per-user data dir/ZeusAgent)")
    parser.add_argument("--plan", action="store_true", help="verify and print, write nothing")
    parser.add_argument("--uninstall", action="store_true", help="remove what the receipt created")
    parser.add_argument("--yes", action="store_true", help="confirm --uninstall")
    parser.add_argument("--purge-data", action="store_true",
                        help="with --uninstall: delete the isolated HERMES_HOME too")
    args = parser.parse_args(argv)

    root = Path(args.root) if args.root else default_root()
    if args.uninstall:
        return uninstall(root, confirmed=args.yes, purge_data=args.purge_data)

    checkout, reason = verify_checkout(Path(args.checkout))
    if checkout is None:
        return _refuse(reason or "unverified checkout")
    reason = validate_root(root, checkout)
    if reason:
        return _refuse(reason)

    if args.plan:
        for line in _plan_lines(checkout, root.expanduser().resolve()):
            _say(line)
        return 0
    try:
        return install(checkout, root)
    except (OSError, RuntimeError) as exc:
        print(f"{PREFIX} failed: {exc}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
